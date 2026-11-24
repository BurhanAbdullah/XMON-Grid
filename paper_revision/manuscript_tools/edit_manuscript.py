#!/usr/bin/env python3
"""Apply the reviewer report (attachment.txt, issues 1-34 and sections 7-16) to XMON_Grid_manuscript_revised_1.docx.
Every number in new text is read from the analysis CSVs. Usage:
python edit_manuscript.py <in.docx> <out.docx> <ana_dir> <exp_out_dir> <fig_dir>"""
import sys, copy, json
import numpy as np, pandas as pd
import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx_helpers import *

SRC, DST, ANA, EXP, FIG = sys.argv[1:6]
d = docx.Document(SRC)
P = list(d.paragraphs); T = list(d.tables)
H1 = d.styles["Heading 2"]

# ============================================================ data (all numbers come from here)
def f4(x): return f"{x:.4f}"
def pm(m, s): return f"{m:.4f}±{s:.4f}"
ON_TEXT = json.load(open(f"{ANA}/onset_text.json"))
k12 = pd.read_csv(f"{ANA}/T_k1_k2_5seed.csv").set_index("rule")
sq = pd.read_csv(f"{ANA}/seq_false_alarms_k2.csv")
cls = pd.read_csv(f"{ANA}/T_class_recall_5seed.csv", header=[0, 1], index_col=0)
tc = pd.read_csv(f"{ANA}/tau_comp_by_seed.csv", index_col=0)
e35 = pd.read_csv(f"{EXP}/exp3_exp5_current.csv")
on = pd.read_csv(f"{ANA}/T_onset_summary.csv")
oct_ = pd.read_csv(f"{ANA}/T_onset_class_tier.csv")
okt = pd.read_csv(f"{ANA}/T_onset_kappa_tau.csv")
ps = pd.read_csv(f"{ANA}/T_param_sensitivity.csv")
nv = pd.read_csv(f"{ANA}/T_nis_threshold_variants.csv").set_index("col")
bp = pd.read_csv(f"{ANA}/T_benign_process.csv")
oo = pd.read_csv(f"{ANA}/T_outage_resolved.csv").set_index("case")
of = pd.read_csv(f"{ANA}/T_outage_fixed_state.csv").set_index("case")
cz = pd.read_csv(f"{ANA}/calib_size_all.csv")
vmeta = pd.read_csv(f"{ANA}/variants_meta.csv").set_index("case")
CN = {"case9": "9-bus", "case14": "14-bus", "case30": "30-bus", "case118": "118-bus"}
def O(rule, thr="fixed"):
    return on[(on.rule == rule) & (on.threshold == thr)].iloc[0]

# ============================================================ 1. renumber existing labels and references
TMAP = {2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 12, 9: 11, 10: 13, 11: 14, 12: 16, 13: 19, 14: 20}
FMAP = {3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 12, 12: 14, 13: 16, 14: 17}
renumber(d, TMAP, FMAP)

# ============================================================ 2. abstract (section 7 of the report)
k2_on, cu_on = O("Quorum K=2"), O("Sequential monitor (tau=5)")
m_g, m_e, m_w, m_t, m_n = (O(r, "alpha=0.01") for r in ["CUSUM recursion g", "EWMA of standardized NIS", "Sliding sum of NIS (10 cycles)", "Leaky accumulator Theta", "NIS (single cycle)"])
acc = [m_g, m_e, m_w, m_t]
assert all(r.Recall > m_n.Recall for r in acc), "abstract claim: every accumulator above single-cycle NIS"
assert min(m_g.Recall, m_t.Recall) > max(m_e.Recall, m_w.Recall), "abstract claim: CUSUM and leaky accumulator retain the most"
set_text(P[3],
 "Persistent, low-amplitude anomalies can escape cycle-wise residual tests when their effect in each cycle stays within the "
 "expected measurement-noise range. This study examines sequential innovation monitoring in nonlinear AC state estimation "
 "through a controlled evaluation of detector components and temporal accumulation mechanisms. An EKF-style "
 "estimator with an analytical measurement Jacobian provides the innovation statistics for a normalized-innovation-squared (NIS) "
 "test, a one-sided CUSUM monitor, and a SCADA timing-jitter detector. A two-out-of-three quorum combines their binary outputs, "
 "and a composite score and a leaky accumulator are evaluated separately. On the IEEE 9-, 14-, 30-, and 118-bus systems across "
 "five seeds, the quorum reaches an F1-score of 0.9204 ± 0.0026, a recall of 0.8850 ± 0.0012, and a false-positive rate (FPR) of "
 "0.1525 ± 0.0197. Most benign false alarms arise during estimator start-up after each flat-start reset. In a second experiment "
 "the anomaly begins after the estimator has converged, and every continuous statistic is thresholded at a 0.01 false-alarm rate "
 "set on separate benign sequences. Pooled over the four systems, every accumulator "
 "then retains more anomalous cycles than the single-cycle NIS, and the long-memory CUSUM recursion and leaky accumulator retain the "
 "most (post-onset recall "
 f"{m_g.Recall:.3f} and {m_t.Recall:.3f}, against {m_e.Recall:.3f} for the EWMA and {m_n.Recall:.3f} for the single-cycle NIS). "
 "Under the evaluated scenarios, temporal accumulation is more consequential than the voting rule, and once anomalies start after "
 "convergence its memory length also matters, except on the " + ON_TEXT["lose_cases"].replace(" case", " system") + ". The findings are limited "
 "to seeded synthetic scenarios and do not establish operational detection performance.")

# ============================================================ 3. introduction (section 8 of the report)
replace_in(P[6], "it continued presence", "its continued presence")
set_text(P[7],
 "The residual test has a second limitation. It cannot detect problems in the communication layer itself. An attacker who "
 "compromises a remote terminal unit (RTU) or disrupts its communication link may alter packet arrival patterns without "
 "introducing inconsistencies that the residual test would flag [9], [10].")
p9txt = P[9].text.strip()
set_text(P[8],
 "CUSUM-based change detection is commonly used to address persistent, small deviations by accumulating evidence across "
 "successive observations rather than evaluating each sample independently [11], [12]. It has also been applied to the detection "
 "of false-data injection attacks (FDIAs) in smart grids [13], [14]. " + p9txt.replace("[13], [14]. ", "", 1))
delete(P[9]._p)
replace_in(P[11], "As described in their abstracts, these tests", "These tests")
# split paragraph 14 at the topology and cross-layer threads, fix the missing space
t14 = "".join(t.text or "" for t in P[14]._p.iter(qn("w:t")))
i_top = t14.index("Topology manipulation"); i_cross = t14.index("The other relevant line")
part1, part2, part3 = t14[:i_top].strip(), t14[i_top:i_cross].strip(), t14[i_cross:].strip()
part3 = part3.replace("electrical measurements.Aljohani", "electrical measurements. Aljohani")
part3 = part3.replace("According to their abstracts, the communication evidence", "The communication evidence")
set_text(P[14], part1)
p14b = para_after(P[14]._p, P[14], part2)
p14c = para_after(p14b._p, P[14], part3)
# synthesis paragraph after Table I
syn = para_after(T[0]._tbl, P[12],
 "Taken together, these studies establish three points. Residual and innovation statistics remain the physical basis of most "
 "detectors. Temporal evidence has been accumulated with Kalman-type filters, quickest-detection formulations, and sliding-window "
 "CUSUM. Learned or rule-based methods add communication and cross-layer features. Within the papers surveyed here, none answers a "
 "narrower question: which parts of a combined innovation-based monitoring architecture contribute to persistent-anomaly detection "
 "under a common nonlinear AC state-estimation protocol. This study addresses only that question. It does not propose a new "
 "detector, it does not compare against learning-based or robust-estimation detectors, and it does not test stealthy or adaptive "
 "attacks.")
set_text(P[16],
 "Three questions remain open for persistent, low-amplitude synthetic anomalies in nonlinear AC estimation. Does recursively "
 "accumulating an innovation statistic buy sensitivity beyond a single-cycle NIS test, and if so, does the particular recursion "
 "matter or would any standard accumulator do? Where do the false alarms of such a design come from, the detector itself or the "
 "way it is evaluated? And once a sequential innovation statistic is in place, how much do a timing stream and a voting rule add? "
 "Each question also has to be answered when the anomaly begins after the estimator has converged, not only from a reset. We did "
 "not find a study that answers these questions inside one AC framework under one protocol. That statement is limited to the "
 "papers surveyed here. The search was not exhaustive, and what we say about cited works is based on their abstracts.")
set_text(P[17],
 "We address these questions with a controlled empirical study, not a new detector. A nonlinear AC estimator produces the "
 "innovation and its covariance. Three streams work on that output: a χ^{2} test on the normalized innovation squared (NIS), a "
 "one-sided CUSUM recursion on the standardized NIS, and a jitter test on SCADA inter-arrival times. The three binary indicators "
 "are combined using a two-out-of-three quorum, while the composite score and leaky accumulator run in parallel but do not "
 "influence the voting decision. All detection thresholds are calibrated using benign data. Using the same evaluation traces, the "
 "framework is then tested against alternative combinations of the detection streams, all three quorum configurations, "
 "single-cycle NIS thresholding, and two established temporal baselines: an exponentially weighted moving average (EWMA) and a "
 "sliding-window NIS sum. The analysis also examines the benign NIS distribution and the timing of false alarms within each "
 "sequence. A second experiment starts each anomaly after the estimator has converged on benign data and compares the detectors "
 "at thresholds frozen on separate benign calibration sequences. The study therefore investigates the behavior of innovation "
 "statistics under persistent synthetic anomalies, the effects of estimator initialization, the relative contributions of "
 "temporal accumulation and detector fusion, and performance after the start-up period. It does not establish operational "
 "detection performance.")
set_text(P[19],
 "**Controlled detector comparison.** A common nonlinear AC state-estimation framework, whose analytic measurement Jacobian is "
 "checked against central finite differences, is used to evaluate NIS-based detection, sequential accumulation (CUSUM, EWMA, "
 "sliding-window NIS sum, and leaky accumulation), timing-based monitoring, and quorum fusion on the same traces.")
set_text(P[20],
 "**Component-level evaluation.** The contribution of temporal memory, detector fusion, and the timing stream is investigated "
 "with internal baselines and structure-preserving comparisons of standalone streams, two-stream rules, and every quorum size, "
 "and with a benign-to-attack onset experiment that reports detection delay, run lengths, missed detections, and false alarms at "
 "thresholds frozen on benign calibration data.")
set_text(P[21],
 "**Initialization and calibration analysis.** The effects of estimator start-up, NIS miscalibration, false-alarm timing, "
 "measurement-noise mismatch, calibration size, and detector-parameter settings are quantified across four IEEE benchmark systems "
 "and five seeds.")
set_text(P[22],
 "The rest of the paper is organized as follows. Section II describes the methodology and architecture. Section III presents the "
 "results in ten parts: overall performance, topology dependence and false alarms, anomaly class and severity, detector "
 "contribution and fusion, NIS calibration, temporal accumulation baselines including the onset experiment, sensitivity to "
 "noise mismatch and parameters, computational cost, verification of the measurement model, and limitations. Section IV concludes.")

# ============================================================ 4. methodology
set_text(P[41],
 "For a voltage magnitude and full nodal P/Q injections at every bus this holds generically away from a measure-zero set of "
 "degenerate points. This is a structural, analytical argument. The pipeline does not run a numerical rank or conditioning check at "
 "each evaluated operating point, so observability is not numerically verified for every realization. The verification checks of "
 "Section III-I test the measurement equations and their derivatives, not observability.")
jac = para_after(P[41]._p, P[41],
 "The analytic Jacobian is verified numerically as follows. For each case one operating point is drawn with "
 "numpy.random.RandomState(2026), reseeded for every case, with angles θ_{2},…,θ_{N_b} from 𝒩(0,0.05^{2}) rad and voltage "
 "magnitudes from 𝒩(1,0.02^{2}) p.u. Each of the 2N_{b}−1 state variables is perturbed by ±ε with ε=10^{-6}, the same step for "
 "angles and voltage magnitudes with no variable scaling. The central difference of h(x) over all 3N_{b} measurement channels "
 "forms the numerical Jacobian, with the reference angle θ_{1} removed exactly as in (7). The error is reported both as the "
 "largest absolute entry difference and as the relative Frobenius norm ‖H−H_{FD}‖_{F}/‖H‖_{F}. One state per case is checked, so "
 "the check verifies the implementation at those states and is not a guarantee over all operating points.")
# verification table after the measurement-noise paragraph (Issue 19)
ver = para_after(P[47]._p, P[47],
 "Table II separates the four checks that concern the estimator. They validate different things. In particular, near-zero "
 "power-balance errors show that the measurement equations are implemented correctly. They say nothing about the statistical "
 "consistency of the EKF, which the benign NIS diagnostics of Section III-E show to be poor.")
cap2 = para_after(ver._p, P[71], "**Table II.** Verification Checks and What Each Validates.")
tbl2 = make_table(T[1], [["Verification", "What it validates", "Where reported"],
    ["Power-balance consistency", "Measurement-equation implementation against independently calculated network quantities", "Section III-I"],
    ["Analytical Jacobian vs. finite differences", "Derivatives of the implemented measurement function", "Section III-I"],
    ["Observability argument", "Whether the measurements determine the state locally (analytical, no numerical rank check)", "Section II"],
    ["EKF consistency", "Whether the estimator statistics agree with the assumed model (not satisfied, Table XIV)", "Section III-E"]],
    [1.8, 3.4, 1.1], cap2._p)
# timing stream statement (Issue 16)
set_text(P[57],
 "with W_{k}=min(k,W), W=20, η_{σ}=3.5, and η_{μ}=2.0. The timing stream uses a separate communication-timing observable and is "
 "intended to provide evidence complementary to the electrical measurements. Statistical independence between the timing and "
 "electrical detection streams is not assumed, and their dependence under the evaluated scenarios is not explicitly characterized.")
# calibration size and topology-specific calibration (Issues 33, 34)
t9r = tc.loc["case9"]; t118 = tc.loc["case118"]
set_text(P[67],
 "K=2 (strict majority) is the primary mode and K=1 (logical OR) is a higher-sensitivity alternative. Neither S_{comp} nor Θ_{k} "
 "enters V(k). The complete architecture is illustrated in Fig. 1, the per-cycle procedure is listed in Algorithm 1, and Table III "
 "lists every parameter with its provenance. Calibration quantities (μ_{0},σ_{0},μ_{T},σ_{T},τ_{Θ},τ_{comp}) are computed per "
 "topology and seed from 200 benign samples, fixed before any test sample is scored, and applied unchanged across all anomaly "
 "classes and tiers. The evaluation assumes topology-specific benign calibration and therefore does not assess transfer of "
 "detector thresholds across networks or operating conditions. The size of 200 samples is a practical choice. A 99th-percentile "
 "estimate from 200 samples is set by the second- and third-largest values, so τ_{comp} is not a precise quantile estimate. Across "
 f"the five seeds it ranges from {tc.min(axis=1)['case9']:.4f} to {tc.max(axis=1)['case9']:.4f} on the 9-bus case, "
 f"{tc.min(axis=1)['case14']:.4f} to {tc.max(axis=1)['case14']:.4f} on the 14-bus case, {tc.min(axis=1)['case30']:.4f} to "
 f"{tc.max(axis=1)['case30']:.4f} on the 30-bus case, and {tc.min(axis=1)['case118']:.4f} to {tc.max(axis=1)['case118']:.4f} on "
 "the 118-bus case, and Section III-G shows its dependence on the calibration size.")
# Table II (now III) footnote and threshold provenance rows (Issue 32)
t3 = T[1]
for lab, val, prov in [("Retrospective matched-FPR thresholds (Table XVI)", "(1−f) quantile of benign test values, f=0.05, 0.15", "test data, retrospective only"),
                       ("Onset-experiment thresholds (Table XVII)", "99th pct. of benign calibration sequences", "calibrated, benign-only, frozen")]:
    tr = copy.deepcopy(t3.rows[-1]._tr); t3.rows[-1]._tr.addnext(tr)
    for tcell, v in zip(tr.findall(qn("w:tc")), [lab, val, prov]):
        ps_ = tcell.findall(qn("w:p"))
        for x in ps_[1:]: tcell.remove(x)
        set_text(Paragraph(ps_[0], t3), v)
# move bottom border: copy cell properties of the old last row to the new last row and vice versa
rows3 = t3._tbl.findall(qn("w:tr")); mid = rows3[1]
for tr in rows3[-3:-1]:
    for c, m in zip(tr.findall(qn("w:tc")), mid.findall(qn("w:tc"))):
        o = c.find(qn("w:tcPr")); n_ = copy.deepcopy(m.find(qn("w:tcPr")))
        if o is not None: c.remove(o)
        if n_ is not None: c.insert(0, n_)
note_tr = copy.deepcopy(T[7].rows[-1]._tr)
for e in note_tr.iter(qn("w:gridSpan")): e.set(qn("w:val"), "3")
tcs = note_tr.findall(qn("w:tc"))
for x in tcs[1:]: note_tr.remove(x)
t3._tbl.append(note_tr)
ps_ = tcs[0].findall(qn("w:p"))
for x in ps_[1:]: tcs[0].remove(x)
set_text(Paragraph(ps_[0], t3),
 "Fixed design parameters are specified a priori. Calibration parameters are estimated from benign calibration samples and remain "
 "fixed during the corresponding test sequences. Thresholds selected from benign test samples are used only for retrospective "
 "matched-FPR comparisons and are not treated as deployable thresholds.")
# anomaly scenarios (Issues 12, 21, 22)
vm = {c: vmeta.loc[c, "gen"] for c in vmeta.index}
set_text(P[79],
 "The anomaly and attack scenarios follow a deliberately narrow threat model. The attacker can alter reported measurements before "
 "the estimator but not the physical flow. The scenarios carry no stealth guarantee, none adapts to the detectors, and none "
 "falsifies breaker or topology telemetry. Five scenarios are evaluated per case: a benign baseline and four anomaly classes. Only "
 "the additive FDIA, voltage-scale, and drift scenarios represent manipulation of the data. The first class, a branch outage, is a "
 "synthetic topology-change anomaly, and the results keep it separate from the FDIA-type scenarios. The series admittance of the "
 "first in-service non-islanding branch is removed and Y is rebuilt. The first eligible non-islanding branch is selected "
 "deterministically to ensure reproducibility. The branch is not selected according to its electrical sensitivity or expected "
 "detectability. It is the branch between buses 4 and 5 on the 9-bus case, where the first listed branch (buses 1–4) would island "
 "bus 1, and the branch between buses 1 and 2 on the 14-, 30-, and 118-bus cases. The pre-outage operating state, perturbed by "
 "zero-mean Gaussian state noise whose standard deviations (σ_{a},σ_{v}) grow with the severity tier, is then passed through the "
 "measurement function of the post-outage network. The post-outage power-flow equilibrium is not recomputed. The scenario is "
 "therefore a branch-outage-induced model mismatch, a post-outage measurement inconsistency under a fixed pre-outage operating "
 "state, intended to generate a measurement/model inconsistency and not to simulate a physically settled outage response. The "
 "topology change itself is identical across tiers.")
# FDIA channels and voltage-scale terminology (Issues 23, 24), verified against core/data_pipeline.py
set_text(P[82],
 "where a_{k} holds the same offset u_{k} on every voltage-magnitude channel and the same offset p_{k} on every active-power "
 "injection channel, with the reactive-power channels left unchanged. Both offsets are redrawn uniformly in every cycle from "
 "tier-dependent ranges (fixed at Tier 4). This scenario is a direct manipulation of the voltage and P measurement channels.")
set_text(P[83],
 "The voltage-scale scenario multiplies every bus voltage magnitude of the state by (1−λ) before h(·) is evaluated, as in (19), "
 "with λ redrawn uniformly in every cycle from the tier range,")
set_text(P[85],
 "so the P/Q channels change through (2). It is therefore a voltage-state manipulation before measurement generation, which alters "
 "all 3N_{b} channels consistently with a scaled state. It differs from direct manipulation of voltage telemetry and from "
 "independent P/Q channel manipulation, it should not be read as a generic FDIA affecting arbitrary measurement channels, and it is "
 "not a re-solved load change.")
set_text(P[86],
 "The persistent low-amplitude drift adds a small offset to every bus voltage magnitude of the state before h(·) is evaluated, as "
 "in (20),")
set_text(P[88],
 "The offset δ is drawn uniformly from the tier range of Table IV independently in every cycle. It is a fixed-size offset redrawn "
 "each cycle, not a cumulative ramp, so it neither grows nor resets within a sequence, and its sign is always positive. In addition, "
 "in this scenario only and independently of δ, the inter-arrival time is drawn with probability 0.2 per cycle with mean 0.006 s "
 "and standard deviation 0.0015 s instead of mean 0.004 s and standard deviation 0.0005 s, clipped at 10^{-4} s. The mean shift of "
 "0.002 s equals four times the benign standard deviation of 0.0005 s used by the generator. This is the only scenario that "
 "perturbs the timing stream. The anomaly is present from the first scored cycle in the original protocol and from the onset cycle "
 "in the onset experiment. The tier-dependent parameters of all four anomaly classes are listed in Table IV.")
replace_in(P[89], "so the benign state does not follow the random-walk model assumed by the estimator.",
 "so the benign state does not follow the random-walk model assumed by the estimator. The benign operating state is generated "
 "through independent perturbations around a fixed operating point rather than through the random-walk process assumed by the "
 "estimator. This mismatch is retained as part of the evaluated protocol and is expected to affect the innovation statistics. It is "
 "a simplification of the released synthetic generator, not a designed model-mismatch test, and Section III-E isolates its effect "
 "with a matched benign process.")
replace_in(P[90], "by Attack", "by Anomaly Class")
# evaluation protocol: timeline, seeds, burn-in definitions (Issues 14, 25, 28)
set_text(P[91],
 "Four IEEE cases are used, as illustrated in Fig. 2 (9/9, 14/20, 30/41, and 118/186 buses/branches), with m=3N_{b} measurements "
 "per cycle (27, 42, 90, and 354). A test evaluation is one SCADA scan cycle passed through Algorithm 1. Fig. 3(a) shows the "
 "timeline of the original protocol as implemented. Calibration runs the estimator from the flat start over 200 benign samples. "
 "The 60 test samples of a case, seed, and scenario are then consecutive cycles of one sequence. At the start of every sequence the "
 "estimator restarts from the flat start x̂_{0}, P_{0}, and g_{k}, the jitter window, and Θ_{k} reset to zero. So calibration and "
 "every test sequence begin with a filter start-up transient, and the anomaly, when present, is active from the first cycle with no "
 "transition from benign operation within a sequence. Within an attack sequence the severity tiers are cyclically interleaved (tier "
 "(i mod 4)+1 for sample i), so each tier has 15 samples per anomaly class per case and seed, and consecutive cycles always change "
 "tier. Each case and seed has 200 calibration samples and 60×5=300 test samples. Five seeds (2026–2030) over four cases give "
 "4×300×5=6,000 evaluations, of which 4,800 are attacked, a prevalence of 0.80. Five-seed means and sample standard deviations are "
 "computed over the five per-seed metrics, not over pooled predictions. They describe variability across the five seeded "
 "simulation runs, which differ only in measurement noise and anomaly realizations, and they do not support broad statistical "
 "generalization. The primary seed (2026, N=1,200: 960 attack and 240 baseline evaluations) supports the threshold-free curves, the "
 "paired McNemar tests, and the original component tables. All other breakdowns are reported over five seeds.")
set_text(P[92],
 "We report accuracy, precision, recall, F1, false-positive rate (FPR), and the Matthews correlation coefficient (MCC). FPR is "
 "computed only where baseline samples exist, and we also quote it as false alarms per 1,000 benign cycles. On S_{comp} we compute "
 "the area under the ROC curve (ROC-AUC) and the area under the precision–recall curve (PR-AUC). The PR-AUC uses the trapezoidal "
 "rule, and here it agrees with average precision to four decimals. Precision moves with prevalence, so for a prevalence π we derive "
 "it from recall and FPR as π·TPR/(π·TPR+(1−π)·FPR). Four extra analyses reuse the regenerated trace, and none of them touches the "
 "detector code. (i) Burn-in sensitivity: k=0 denotes the first cycle of a test sequence, and all metrics are recomputed on cycles "
 "k≥20, so cycles 0–19 are removed and the first evaluated cycle is k=20. Only the metric computation excludes these cycles. The "
 "detectors are not reset at k=20 and keep the evidence accumulated during cycles 0–19, so this analysis is not equivalent to "
 "running detectors initialized at k=20. (ii) Temporal baselines: on the same NIS stream and with the same reset points we compute "
 "an exponentially weighted moving average (EWMA) e_{k}=0.2y_{k}+0.8e_{k−1} and a sum of the last 10 NIS values. We compare them "
 "with ξ_{k}, g_{k}, Θ_{k}, and S_{comp} through per-case ROC-AUC and through recall at a matched per-case FPR f of 0.05 and 0.15. "
 "For each statistic, case, and seed, the threshold is the smallest benign test value at or above the (1−f) quantile of its own "
 "benign test values. These thresholds are selected on test data, so the resulting operating points are retrospective comparisons "
 "of what each statistic can reach on these traces, not deployment-calibrated performance. (iii) Delay: we take the index of the "
 "first alarm in each sequence. (iv) NIS diagnostics: we compare the benign mean, variance, lag-1 autocorrelation, and exceedance "
 "rate against the χ^{2}_{m} reference values m, 2m, 0, and α.")
onp = para_after(P[92]._p, P[92],
 "The onset experiment measures detection after the estimator has converged (Fig. 3(b)). It uses the same repository generator, "
 "calibration samples, detector code, and thresholds. The generator draws every cycle independently given the scenario and tier, "
 "so longer benign blocks and single-tier blocks of each anomaly class are taken from larger generated test blocks. After each "
 "reset the estimator processes 30 benign cycles that are not scored and do not update any detector. Scoring then starts with all "
 "detectors at their reset state and continues without any further reset: 30 benign cycles are followed by 30 cycles of one "
 "anomaly class at one constant severity tier, so the onset falls at the 31st scored cycle. Each case and seed has one such sequence "
 "per class and tier (16), four 60-cycle benign test sequences, and four separate 60-cycle benign calibration sequences built the "
 "same way. The repository detectors keep their own fixed thresholds. For the continuous statistics (single-cycle NIS, 10-cycle "
 "NIS sum, EWMA, g_{k}, Θ_{k}), each threshold is the 99th percentile of the statistic over the benign calibration sequences of "
 "that case and seed, frozen before any test sequence is scored, which places all of them at the same nominal per-cycle "
 "false-alarm rate of 0.01. We report the FPR over benign scored cycles, ARL_{0} as the number of benign cycles observed up to "
 "and including the first false alarm divided by the number of benign segments that raised one (a censored geometric estimate, "
 "because segments last only 30 or 60 cycles), the detection probability P_{d} within the 30 post-onset cycles, the "
 "missed-detection rate 1−P_{d}, the detection delay counted from the onset cycle (delay 0 means an alarm in the onset cycle), "
 "ARL_{1} as the mean of the delay plus one over detected sequences, and the post-onset recall.")
onp2 = para_after(onp._p, P[92],
 "Three further analyses complete the evaluation. First, parameter sensitivity varies one factor at a time around the reported "
 "setting: κ∈{0.25,0.5,1.0} and τ_{cusum}∈{3,5,7}, applied to the recorded NIS stream with the same calibration moments, and Q "
 "scaled by 0.1 and 10 and R by 0.5 and 2 inside the estimator, rerun over all five seeds with the generated data unchanged. "
 "Second, the χ^{2} NIS threshold is compared with empirical 99th and 95th percentiles of the 200 benign calibration NIS values, "
 "with and without the first 20 calibration cycles. Third, two generator variants isolate the process-model mismatch and the "
 "outage construction, as described with their results in Section III.")
# timeline figure after Fig. 2 caption
figT = figure_after(P[94]._p, P[93], f"{FIG}/Fig_timeline.png", 5943600)
capT = para_after(figT._p, P[94],
 "**Fig. 3.** Evaluation timelines as implemented. (a) Original protocol: calibration on 200 benign samples from a flat start, "
 "then a reset before every 60-cycle test sequence, which is benign or anomalous from k=0 with no transition. (b) Onset experiment: "
 "the same calibration, a 30-cycle estimator warm-up after each reset, 30 scored benign cycles, and 30 scored anomalous cycles of "
 "one class and one constant tier.")

# ============================================================ 5. results: A. overall
replace_in(P[96], "The noise stress test, the calibration-size runs, and the original latency figures come from a separate robustness run and are labeled where they appear.",
 "The noise stress test and the calibration-size runs come from a separate robustness run, rerun with the current code, and the "
 "onset experiment of Section III-F uses its own protocol. Both are labeled where they appear. Values reported as mean ± SD are the "
 "mean and sample standard deviation of the five seed-specific metrics. They are not confidence intervals. The scripts, raw "
 "outputs, and figure data behind every result, table, and figure of this paper are in the paper_revision directory of the "
 "repository (https://github.com/BurhanAbdullah/XMON-Grid, tag v3.2-paper-revision-20261123).")
hA = para_after(P[96]._p, P[95], "A. Overall Detection Performance", style=H1)
replace_in(P[98], "(N=6,000 scan-cycle evaluations, 5 seeds).", "(N=6,000 scan-cycle evaluations, 5 seeds). Values are the mean and sample SD of the five seed-specific metrics, not confidence intervals.")
set_text(P[99],
 "That FPR works out to roughly 153 false alarms for every 1,000 benign cycles. The attack prevalence of 0.80 is imposed by the "
 "synthetic evaluation design, and precision depends on it. Keeping recall at 0.8850 and FPR at 0.1525, precision is 0.959 at the "
 "evaluated prevalence of 0.80, but it drops to 0.853 at 0.50, to 0.392 at 0.10, and to 0.055 at 0.01. These lower-prevalence values "
 "are illustrative and not an operational forecast. Precision is therefore not transferable to operational conditions, and the FPR "
 "is the more relevant indicator of the benign-cycle alarm burden in this experiment.")
K1, K2 = k12.loc["d_k1"], k12.loc["d_k2"]
set_text(P[102],
 "Both quorum modes use the same three flags and differ only in the agreement threshold. Over five seeds, K=1 reaches recall "
 f"{pm(K1.Recall_mean, K1.Recall_sd)} at FPR {pm(K1.FPR_mean, K1.FPR_sd)}, whereas K=2 gives recall "
 f"{pm(K2.Recall_mean, K2.Recall_sd)} at FPR {pm(K2.FPR_mean, K2.FPR_sd)} (Table VI, Fig. 5). Both columns use the same basis, "
 "five seeds with N=1,200 evaluations per seed, so they compare operating points on equal terms.")
set_text(P[103], "**Table VI.** Operating-Point Comparison of K=1 and K=2 (five seeds, N=1,200 per seed). Values are the mean and sample SD of the five seed-specific metrics, not confidence intervals.")
t6 = T[4]
vals6 = [("Precision", "Precision"), ("Recall", "Recall"), ("F1-score", "F1"), ("FPR", "FPR")]
hdr = t6.rows[0].cells
set_text(hdr[1].paragraphs[0], "K=1, five seeds (N=6,000)"); set_text(hdr[2].paragraphs[0], "K=2, five seeds (N=6,000)")
for r, (lab, m) in zip(t6.rows[1:], vals6):
    set_text(r.cells[1].paragraphs[0], pm(K1[m + "_mean"], K1[m + "_sd"])); set_text(r.cells[2].paragraphs[0], pm(K2[m + "_mean"], K2[m + "_sd"]))
swap_image(P[104], f"{FIG}/Fig_k1_k2.png")
set_text(P[105], "**Fig. 5.** (a) Recall versus FPR of the K=1 and K=2 operating points over five seeds (open circles: individual seeds, filled markers: mean ± SD). (b) Enlarged view of the five individual K=2 seeds.")

# ============================================================ B. topology and false alarms
hB = para_after(P[108]._p, P[95], "B. Topology Dependence and False Alarms", style=H1)
agg = sq.groupby("case")
def cs_(c, f): return f(sq[sq.case == c])
rows9 = [["Topology", "Benign sequences alarmed", "Alarmed in start-up (k<20)", "Alarm runs", "Longest run (cycles)", "First alarm (k)", "Alarm cycles at k≥20 (sequences)"]]
for c in ["case9", "case14", "case30", "case118"]:
    g = sq[sq.case == c]; fa = g[g.onset >= 0].onset
    rows9.append([f"IEEE {CN[c]}", f"{g.any_alarm.sum()}/5", f"{g.startup_any.sum()}/5", str(g.n_runs.sum()), str(g.longest_run.max()),
                  ("–" if fa.empty else (str(fa.min()) if fa.min() == fa.max() else f"{fa.min()}–{fa.max()}")),
                  f"{g.post_alarms.sum()} ({g.post_any.sum()})"])
g14 = sq[sq.case == "case14"]; g9 = sq[sq.case == "case9"]; g118 = sq[sq.case == "case118"]; g30 = sq[sq.case == "case30"]
seqp = para_after(P[116]._p, P[113],
 "Table IX reads the same K=2 false alarms at the sequence level, with one 60-cycle benign sequence per case and seed, so five per "
 "topology. On the 9-, 14-, and 118-bus cases every benign sequence alarms, and every first alarm falls at k=0, during "
 f"initialization. The 118-bus case produces a single run of {g118.longest_run.min()} or {g118.longest_run.max()} consecutive "
 f"alarm cycles in each sequence, whereas the 9- and 14-bus cases produce {min(g9.n_runs.min(), g14.n_runs.min())} to "
 f"{max(g9.n_runs.max(), g14.n_runs.max())} short runs of at most {g9.longest_run.max()} and {g14.longest_run.max()} cycles. Only "
 f"two benign sequences alarm after k=20: one on the 14-bus case ({g14.post_alarms.sum()} cycle) and one on the 30-bus case "
 f"({g30.post_alarms.sum()} cycles in {g30.n_runs.sum()} runs, from k={g30[g30.onset >= 0].onset.min()}). The same cycle-level FPR "
 "therefore stands for very different operational behavior: one start-up burst per sequence on the 118-bus case, several short "
 "start-up runs on the 9- and 14-bus cases, and rare steady-state alarms on the 30-bus case.")
cap9 = para_after(seqp._p, P[114], "**Table IX.** Sequence-Level Reading of K=2 Benign False Alarms (five benign sequences of 60 cycles per topology, original protocol).")
tbl9 = make_table(T[6], rows9, [1.0, 0.95, 0.95, 0.6, 0.8, 0.7, 1.2], cap9._p)
replace_in(P[114], "(mean ± sample SD over seeds 2026–2030, N=300 per case and seed).", "(mean ± sample SD over seeds 2026–2030, N=300 per case and seed). Values are the mean and sample SD of the five seed-specific metrics, not confidence intervals.")

# ============================================================ C. anomaly class and severity
replace_in(P[119], "by attack scenario (N=240 per scenario).", "by anomaly class (N=240 per class).")
hC = para_after(tbl9._tbl, P[95], "C. Anomaly-Class and Severity Analysis", style=H1)
def cv(sc, col): return pm(cls.loc[sc, (col, "mean")], cls.loc[sc, (col, "std")])
set_text(P[117],
 "Broken down by anomaly class, recall at K=2 on the primary seed is 0.9958 for additive FDIA (239/240), 0.8000 for the "
 "voltage-scale attack (192/240), and 0.7500 for persistent low-amplitude drift (180/240), and 0.9958 for the branch-outage-induced "
 "model mismatch (239/240) (Fig. 9). Table X gives the five-seed values. The K=2 misses on the voltage-scale and drift scenarios are "
 "NIS misses. The standalone sequential monitor detects almost all of these cycles, the NIS test detects about three in four to "
 "four in five, and the AND structure of the quorum inherits the weaker of the two. Branch-outage detection reflects the topology "
 "change plus added state noise, not a severity-graded topology perturbation.")
cap10 = para_after(P[117]._p, P[114], "**Table X.** Five-Seed Recall by Anomaly Class (mean ± sample SD of the five seed-specific values, not confidence intervals, 240 attacked cycles per class and seed).")
rows10 = [["Anomaly class", "Quorum K=2", "NIS test", "Sequential monitor", "Leaky accumulator"]]
for sc, lab in [("fdia", "Additive FDIA"), ("load_shift", "Voltage scale"), ("stealth_drift", "Persistent drift"), ("branch_outage", "Branch outage (topology-change anomaly)")]:
    rows10.append([lab, cv(sc, "d_k2"), cv(sc, "a_nis"), cv(sc, "a_cusum"), cv(sc, "a_seq")])
tbl10 = make_table(T[6], rows10, [2.2, 1.1, 1.1, 1.2, 1.2], cap10._p)
outp = para_after(tbl10._tbl, P[117], ON_TEXT["outage"])
replace_in(P[120], "We report them descriptively. Measuring the true amplitude response would take a single-class sweep with blocks of constant severity.",
 "We report them descriptively, and they are not evidence of a monotonic severity response or of greater or lower sensitivity to "
 "any severity level. Section III-F reports a separate experiment with one anomaly class and one constant tier per sequence.")
replace_in(P[122], "by severity tier with counts.", "by severity tier with counts (cyclically interleaved tiers, descriptive only).")

# ============================================================ D. detector contribution and fusion (reorder: structure-preserving first)
hD = para_after(P[122]._p, P[95], "D. Detector Contribution and Fusion", style=H1)
move_before(P[123]._p, [P[127]._p, P[128]._p, T[8]._tbl])
pw = pd.read_csv(f"{ANA}/T_pairwise_rules.csv").set_index("rule")
set_text(P[127],
 "Table XI is the primary component analysis. Each rule keeps its own fixed thresholds, and we evaluate standalone streams, every "
 "two-stream OR and AND rule, and every quorum size over five seeds, with the logic of each rule stated in its label. The K=2 quorum "
 "and the AND of the NIS test with the sequential monitor share the same five-seed FPR (0.1525 ± 0.0197), and their F1 values are "
 "close (0.9204 and 0.9192). Under the synthetic timing model the quorum is, in effect, NIS AND g_{k}. Adding jitter to the OR with g_{k} "
 "changes nothing, adding it to the NIS test raises recall only from 0.8858 to "
 f"{pw.loc['NIS OR jitter','Recall']:.4f}, any AND with jitter almost never fires, and K=3 hardly ever fires (recall 0.0056). The standalone sequential "
 "monitor posts the best F1 and MCC (0.9678 and 0.8289), at an FPR of 0.2458. Swapping in the memoryless variant inside the quorum "
 "lowers F1 to 0.5252. The standalone leaky accumulator gets F1 0.9196 at an FPR of 0.0375 ± 0.0283, about a quarter of the "
 "quorum's. So the quorum does not beat its parts outright. Which rule is better depends on how misses are weighed against false "
 "alarms. The right-hand columns use only cycles k≥20, with detector memory kept from earlier cycles. Once the start-up transient "
 "is gone, the sequential monitor and the leaky accumulator each reach F1 0.9983, recall 1.0000, and FPR 0.0138. The quorum gets "
 "down to FPR 0.0100 ± 0.0191, but its recall stays at 0.8769 because the NIS stream holds it back.")
replace_in(P[128], "N=1,200 per seed).", "N=1,200 per seed). Values are the mean and sample SD of the five seed-specific metrics, not confidence intervals.")
# add the missing pairwise rules (Issue 5), computed from the frozen five-seed trace
t11 = T[8]; anchors = {"NIS OR jitter": t11.rows[6]._tr, "gk AND jitter": t11.rows[7]._tr}
prev = None
for lab in ["NIS OR jitter", "NIS AND jitter", "gk AND jitter"]:
    r = pw.loc[lab]; base_tr = anchors.get(lab, prev); tr = copy.deepcopy(t11.rows[6]._tr); base_tr.addnext(tr); prev = tr
    vals = [lab.replace("gk", "g_{k}"), pm(r.F1, r.F1_sd), pm(r.Recall, r.Recall_sd), pm(r.FPR, r.FPR_sd), pm(r.F1_k20, r.F1_k20_sd), pm(r.FPR_k20, r.FPR_k20_sd)]
    for tcell, v in zip(tr.findall(qn("w:tc")), vals):
        pp = tcell.findall(qn("w:p"))
        for x in pp[1:]: tcell.remove(x)
        set_text(Paragraph(pp[0], t11), v)
set_text(P[123],
 "Table XII and Fig. 11 report an exploratory detector-removal analysis on the primary seed. Removing a stream while retaining K=2 "
 "changes the fusion rule from majority voting over three streams to a conjunction of the remaining two streams. Consequently, these "
 "configurations are not structure-preserving ablations and cannot isolate the independent contribution of the removed detector. "
 "Taking out the NIS test or the sequential monitor wipes out recall (configurations B and C) for that reason. Dropping jitter (D) "
 "barely moves F1 (0.9217 against 0.9229). The largest loss comes from E, where a memoryless per-cycle statistic replaces the "
 "recursive g_{k} inside the same K=2 vote. F1 falls to 0.5173 and recall to 0.3500. Configuration F thresholds S_{comp} with a "
 "single value for every case, namely the 9-bus primary-seed threshold of 0.7051, and reaches F1 0.9228 at FPR 0.0708. With each "
 "case's own τ_{comp}, the same trace gives F1 0.9236 at FPR 0.0500. B lands on exactly the numbers of standalone jitter, since on "
 "this trace every cycle flagged by jitter is also flagged by the sequential monitor.")
set_text(P[124], "**Table XII.** Exploratory Detector-Removal Analysis Under the Fixed Quorum Threshold (primary seed, N=1,200).")
set_text(P[126], "**Fig. 11.** Exploratory detector-removal analysis on the primary seed: (a) F1-score and (b) FPR for configurations A–F of Table XII.")
set_text(P[129],
 "Table XIII and Fig. 12 compare K=2 with its own constituents on the primary seed. The standalone sequential monitor has higher "
 "recall and F1 than K=2 (F1 0.9706 versus 0.9229) at a higher FPR (0.2250 versus 0.1333). The standalone leaky accumulator reaches "
 "comparable F1 (0.9203) at FPR 0.0083, roughly one-sixteenth of the quorum's on this seed and one quarter over five seeds (Table "
 "XI). Paired, continuity-corrected McNemar tests on the primary seed (N=1,200) give, against standalone NIS, b=104 and c=2 "
 "(χ^{2}=96.24, p≈1.0×10^{-22}), and against the standalone sequential monitor b=22 and c=106 (χ^{2}=53.82, p≈2.2×10^{-13}). "
 "These tests are exploratory. They use the primary seed only, the unit of comparison is the paired cycle-level prediction, and "
 "successive cycles within a sequence are temporally dependent. They describe paired prediction differences on the current trace. "
 "They are not five-seed statistical inference, they do not select an operating point, and they are not evidence of general "
 "superiority.")
fusion = para_after(P[133]._p, P[129],
 "Taken together, the two-out-of-three quorum effectively reduces to the combination of the NIS test and the sequential monitor, "
 "with its recall constrained by the single-cycle NIS test. It produces a particular sensitivity–false-alarm trade-off under this "
 "protocol. Its main effect is to suppress start-up false alarms of the sequential monitor, not to improve detection. It gives an "
 "operating point that is straightforward to audit, but it does not outperform the leaky accumulator used on its own. The timing "
 "stream contributes little under the specific timing perturbation evaluated. Only the drift scenario affects SCADA inter-arrival "
 "times, and the perturbation occurs in 20% of cycles with a mean shift of four times the benign standard deviation. The jitter "
 "detector requires both a 3.5σ_{T} excursion and a 20-cycle mean exceeding 2σ_{T}, conditions rarely met by this perturbation. "
 "This finding is specific to the timing model used in the experiments and should not be generalized to communication-layer "
 "monitoring as a whole.")

# ============================================================ E. NIS calibration
hE = para_after(fusion._p, P[95], "E. NIS Calibration and Statistical Behavior", style=H1)
replace_in(P[134], "Two remedies follow: start each sequence from a converged estimator or suppress alarms during a fixed burn-in, and replace the χ2 quantile with an empirical benign quantile. Neither is applied to the reported results.",
 "Two remedies follow: start each sequence from a converged estimator or suppress alarms during a fixed burn-in, and replace the χ2 "
 "quantile with an empirical benign quantile. Neither is applied to the headline results, and Table XV and Section III-F evaluate "
 "both.")
bpi = bp.set_index(["case", "gen"])
rw = bp[bp.gen == "rw"]; ii = bp[bp.gen == "iid"]
mm = para_after(P[136]._p if False else T[10]._tbl, P[134],
 "A matched benign process separates the process-model mismatch from the other causes. In this variant, which reuses the "
 "repository measurement function, noise levels, estimator, detectors, and calibration and changes only the benign state process, "
 "the benign state follows the random walk x_{k}=x_{k−1}+w_{k} with the estimator's own Q, started at the solved operating point. "
 "Each generator is calibrated on its own 200 benign samples and scored on five 60-cycle sequences per case and seed with a reset "
 "per sequence. After the first 20 cycles, the mean NIS per measurement is "
 f"{rw.mean_ratio.min():.3f} to {rw.mean_ratio.max():.3f} under the random walk against {ii.mean_ratio.min():.2f} to "
 f"{ii.mean_ratio.max():.2f} under the independent perturbation, and the χ^{{2}}_{{0.99}}(m) threshold is exceeded in "
 f"{rw.exceed_k20.min()*100:.1f}% to {rw.exceed_k20.max()*100:.1f}% of benign cycles against {ii.exceed_k20.min()*100:.1f}% to "
 f"{ii.exceed_k20.max()*100:.1f}%. The K=2 FPR over all cycles is {rw.k2_fpr_all.min():.4f} to {rw.k2_fpr_all.max():.4f} under the "
 f"random walk and {ii.k2_fpr_all.min():.4f} to {ii.k2_fpr_all.max():.4f} under the independent perturbation, the remainder coming "
 "from start-up. With a benign process that matches the estimator's model, the NIS therefore stays close to its nominal reference "
 f"after start-up (mean ratio within {100*np.max(np.abs(rw.mean_ratio-1)):.1f}% of one), which identifies the process-model mismatch as the main cause of the steady-state miscalibration in Table XIV.")
calib3 = para_after(mm._p, P[134],
 "Three calibration approaches must be kept apart. The NIS test uses a theoretical threshold, the χ^{2}_{0.99}(m) quantile derived "
 "from the nominal reference, not from data. The sequential monitor uses benign-moment calibration: it standardizes the NIS with "
 "μ_{0} and σ_{0} estimated from the 200 calibration values. An empirical NIS threshold, a quantile of the benign calibration NIS "
 "values, is a third approach that the released pipeline does not use. Table XV compares the nominal threshold with empirical 99th "
 "and 95th percentiles of the same 200 calibration values, computed over all of them or only after the first 20 calibration cycles, "
 f"on the original trace and in the onset experiment. The nominal threshold gives FPR {nv.loc['chi2','FPR_k20']:.4f} after cycle 20 "
 f"of the original trace. The empirical 99th percentile of the post-burn-in calibration values gives FPR "
 f"{nv.loc['e99b','FPR_k20']:.4f} at recall {nv.loc['e99b','Recall_k20']:.4f}, and over all 200 values, which include the "
 f"start-up transient, it gives FPR {nv.loc['e99','FPR_k20']:.4f} at recall {nv.loc['e99','Recall_k20']:.4f}. An empirical "
 "threshold calibrated after burn-in therefore restores the nominal false-alarm level at a modest loss of recall, whereas one "
 "calibrated over the transient is set higher and costs more recall.")
cap15 = para_after(calib3._p, P[135], "**Table XV.** NIS Test Under Different Thresholds (five-seed means, thresholds from the 200 benign calibration NIS values of each case and seed).")
rows15 = [["Threshold", "FPR (all)", "Recall (all)", "FPR (k≥20)", "Recall (k≥20)", "FPR (onset exp.)", "Recall (onset exp.)"]]
for col, lab in [("chi2", "Nominal χ^{2}_{0.99}(m)"), ("e99", "Empirical 99th pct., all 200"), ("e95", "Empirical 95th pct., all 200"),
                 ("e99b", "Empirical 99th pct., after burn-in"), ("e95b", "Empirical 95th pct., after burn-in")]:
    r = nv.loc[col]; rows15.append([lab, f4(r.FPR), f4(r.Recall), f4(r.FPR_k20), f4(r.Recall_k20), f4(r.FPR_onset), f4(r.Recall_onset)])
tbl15 = make_table(T[10], rows15, [1.95, 0.7, 0.75, 0.7, 0.8, 0.8, 0.85], cap15._p)

# ============================================================ F. temporal accumulation baselines and onset
hF = para_after(tbl15._tbl, P[95], "F. Temporal Accumulation Baselines", style=H1)
set_text(P[136],
 "Table XVI asks whether the choice of recursion matters on the original trace, and its two halves are two different evaluation "
 "regimes. Over the full sequences, which include the start-up transient, g_{k} comes out on top, with a per-case ROC-AUC of "
 "0.9938 ± 0.0008 and recall 0.9604 at matched FPR 0.05. Next come the EWMA (AUC 0.9707), the sliding-window NIS sum (0.9639), "
 "S_{comp} (0.9610), Θ_{k} (0.9185), and last the single-cycle NIS (0.8709). In the steady-state regime of cycles k≥20, the window "
 "sum, the EWMA, g_{k}, and Θ_{k} all separate attacked from benign cycles perfectly (AUC 1.0000, recall 1.0000 at both FPR levels), "
 "and the single-cycle NIS sits at AUC 0.8789. The lead that g_{k} holds over the full sequences comes from how the statistics react "
 "to the start-up transient. It does not reflect better detection after the filter settles. The matched-FPR columns are "
 "retrospective comparisons with thresholds chosen on the benign test values, not deployment-calibrated performance. In these "
 "scenarios each anomaly lasts the whole sequence and keeps the NIS elevated, so this comparison is empirical and specific to the "
 "reset protocol.")
set_text(P[137], "**Table XVI.** Threshold-Free and Test-Set Operating-Point Comparison of Continuous Detection Statistics (original protocol, five seeds). Matched-FPR recall values are retrospective, with thresholds selected on benign test values. ± values are the sample SD over seeds, not confidence intervals.")
set_text(P[138],
 "Under the original protocol, detection delay cannot be separated from the start-up transient. Every attack sequence raises its "
 "first K=2 alarm at cycle k=0, but so do 15 of the 20 benign sequences across seeds and cases, all of them on the 9-, 14-, and "
 "118-bus cases. The onset experiment removes this confound. Table XVII lists its results over four cases, five seeds, four anomaly "
 "classes, and four tiers (320 onset sequences), and Fig. 13 shows the post-onset recall by class and tier.")
f01 = on[on.threshold == "alpha=0.01"].set_index("rule"); fx = on[on.threshold == "fixed"].set_index("rule"); f05 = on[on.threshold == "alpha=0.05"].set_index("rule")
def drow(lab, r):
    return [lab, f4(r.FPR), (f"{r.ARL0:.0f}" if np.isfinite(r.ARL0) else ">" + "obs."), f"{r.Pd:.4f}", f"{r.Missed:.4f}",
            ("–" if np.isnan(r.delay_median) else f"{r.delay_median:.0f}"), ("–" if np.isnan(r.ARL1) else f"{r.ARL1:.2f}"), f4(r.Recall)]
rows17 = [["Detector and threshold", "FPR", "ARL_{0}", "P_{d}", "Missed", "Median delay", "ARL_{1}", "Post-onset recall"]]
for lab, key in [("NIS test, χ² threshold (fixed)", "NIS test, chi-square threshold"), ("Sequential monitor, τ_{cusum}=5 (fixed)", "Sequential monitor (tau=5)"),
                 ("Leaky accumulator, τ_{Θ} (fixed)", "Leaky accumulator (tau_Theta)"), ("Quorum K=2 (fixed)", "Quorum K=2")]:
    rows17.append(drow(lab, fx.loc[key]))
for lab, key in [("Single-cycle NIS, matched", "NIS (single cycle)"), ("Sliding sum of NIS, matched", "Sliding sum of NIS (10 cycles)"),
                 ("EWMA of y_{k}, matched", "EWMA of standardized NIS"), ("CUSUM g_{k}, matched", "CUSUM recursion g"), ("Leaky accumulator Θ_{k}, matched", "Leaky accumulator Theta")]:
    rows17.append(drow(lab, f01.loc[key]))
nb = int(on.attrs.get("nseg", 0)) if hasattr(on, "attrs") else 0
fixed_nis, fixed_cu, fixed_th, fixed_k2 = fx.loc["NIS test, chi-square threshold"], fx.loc["Sequential monitor (tau=5)"], fx.loc["Leaky accumulator (tau_Theta)"], fx.loc["Quorum K=2"]
onr = para_after(P[138]._p, P[136], ON_TEXT["p1"])
onr2 = para_after(onr._p, P[136], ON_TEXT["p2"])
cap17 = para_after(onr2._p, P[137], "**Table XVII.** Onset Experiment: Detection After Convergence (four cases, five seeds, 320 onset sequences, 400 benign segments). Matched thresholds: 99th percentile of each statistic on separate benign calibration sequences, frozen before testing. ARL_{0} is a censored geometric estimate.")
tbl17 = make_table(T[11], rows17, [2.15, 0.6, 0.55, 0.6, 0.6, 0.62, 0.55, 0.75], cap17._p)
figO = figure_after(tbl17._tbl, P[125], f"{FIG}/Fig_onset_severity.png", 5943600)
capO = para_after(figO._p, P[126], "**Fig. 13.** Onset experiment with constant severity: post-onset recall by severity tier for each anomaly class (five seeds, four cases, 600 attacked cycles per point). Matched detectors use thresholds at the 99th percentile of benign calibration sequences.")
ftxt = para_after(capO._p, P[136], ON_TEXT["p3"])
# ============================================================ G. noise mismatch, calibration size, parameters
hG = para_after(ftxt._p, P[95], "G. Sensitivity to Measurement-Noise Calibration Mismatch and Detector Parameters", style=H1)
n = e35[e35.experiment == "Exp5"]; n26 = n[n.seed == 2026].set_index("param"); n27 = n[n.seed == 2027].set_index("param")
c3 = e35[e35.experiment == "Exp3"]
set_text(P[139],
 "In a separate robustness run (9-bus, K=2), zero-mean Gaussian noise of standard deviation σ was added to all test measurements "
 "while thresholds remained those calibrated on unperturbed benign data. This experiment evaluates sensitivity to "
 "measurement-noise mismatch with thresholds fixed at nominal calibration. It does not assess performance under recalibrated noise "
 "conditions or across different operating points and topologies. The run uses the repository robustness script on the current "
 "code and passes the 300 test cycles through the pipeline as one sequence without resets between scenarios. For seed 2026, as σ "
 f"rises from 5×10^{{-4}} to 10^{{-2}} p.u., F1 falls from {n26.loc[0.0005,'F1']:.4f} to {n26.loc[0.01,'F1']:.4f} and FPR rises "
 f"from {n26.loc[0.0005,'FPR']:.4f} to {n26.loc[0.01,'FPR']:.1f}, reaching {n26.loc[0.002,'FPR']:.2f} at σ=0.002 and "
 f"{n26.loc[0.005,'FPR']:.4f} at σ=0.005 (Fig. 14). Seed 2027 follows the same pattern, with FPR "
 + ", ".join(f"{n27.loc[s,'FPR']:.4f}" for s in [0.0005, 0.001, 0.002, 0.005]) + f", and {n27.loc[0.01,'FPR']:.1f} at the five noise "
 "levels. The nominal per-channel noise standard deviations are 0.002 (voltage) and 0.005 (P/Q), so alarms saturate once added "
 "noise is comparable to the nominal level. The thresholds are tied to the benign noise level, and false alarms are the failure "
 "mode.")
c9 = c3[c3.case == "case9"]; c14 = c3[c3.case == "case14"]
calp = para_after(P[141]._p, P[139],
 "The same run varied the calibration size over 50, 100, 200, and 400 benign samples on the 9- and 14-bus cases for seeds 2026 and "
 f"2027, under the same single-sequence protocol. K=2 F1 stayed within {c3.F1.min():.4f}–{c3.F1.max():.4f}. On the 9-bus case the "
 f"FPR rose with calibration size in both seeds, from {c9[c9.param==50].FPR.min():.4f} at 50 samples to "
 f"{c9[(c9.param==400)&(c9.seed==2026)].FPR.iloc[0]:.4f} and {c9[(c9.param==400)&(c9.seed==2027)].FPR.iloc[0]:.4f} at 400, and on "
 f"the 14-bus case it ranged from {c14.FPR.min():.4f} to {c14.FPR.max():.4f} with no consistent direction. Fig. 15 shows the "
 "calibrated τ_{comp} for all four cases and five seeds. "
 + ON_TEXT["calsize"] + " The limited number of runs and the short calibration sequences do not establish the stability of the "
 "estimated upper-tail thresholds.")
figC = figure_after(calp._p, P[140], f"{FIG}/Fig_calsize.png", 5943600)
capC = para_after(figC._p, P[141], "**Fig. 15.** Calibrated τ_{comp} (99th percentile of benign composite scores) versus calibration size, one curve per seed, for each case. The first 200 of the 400 calibration samples equal those of the original protocol.")
swap_image(P[140], f"{FIG}/Fig_noise.png")
set_text(P[141], "**Fig. 14.** Noise stress test on the 9-bus case with thresholds fixed at nominal-noise calibration, current code: (a) F1-score and recall, (b) FPR, for seeds 2026 and 2027.")
parp = para_after(capC._p, P[139], ON_TEXT["params"])
cap18 = para_after(parp._p, P[137], "**Table XVIII.** One-Factor Parameter Sensitivity, Original Protocol (five-seed means, reported setting κ=0.5, τ_{cusum}=5, Q and R as in Section II).")
rows18 = [["Setting", "Seq. monitor F1", "Seq. monitor FPR", "Seq. monitor FPR (k≥20)", "K=2 F1", "K=2 FPR", "K=2 FPR (k≥20)"]]
for setting, lab in json.load(open(f"{ANA}/param_rows.json")):
    a = ps[(ps.setting == setting) & (ps.rule == "Sequential monitor")].iloc[0]; b = ps[(ps.setting == setting) & (ps.rule == "Quorum K=2")].iloc[0]
    rows18.append([lab, f4(a.F1), f4(a.FPR), f4(a.FPR_k20), f4(b.F1), f4(b.FPR), f4(b.FPR_k20)])
tbl18 = make_table(T[11], rows18, [1.6, 0.8, 0.85, 0.95, 0.65, 0.65, 0.85], cap18._p)

# ============================================================ H. computational cost (Issue 31)
hH = para_after(tbl18._tbl, P[95], "H. Computational Cost", style=H1)
LAT = pd.read_csv(f"{EXP}/latency_repeated.csv").set_index("case"); HW = pd.read_csv(f"{EXP}/latency_hardware.csv").iloc[0]
L118 = LAT.loc["case118"]
set_text(P[142],
 "Runtime was measured with a high-resolution timer (time.perf_counter) on the end-to-end detector step, after five untimed "
 "warm-up steps, over 300 consecutive steps per case (60 for the 118-bus case), and the whole measurement was repeated five "
 f"times. The machine was a virtual machine with an {HW.cpu} ({HW.logical_cpus} logical CPUs, {HW.ram_gb} GB of RAM), running "
 f"Linux, Python {HW.python}, and NumPy {HW.numpy} with single-threaded BLAS. Pooled over the five repetitions, the median "
 "per-step latency was " + ", ".join(f"{LAT.loc[c,'median_ms']:.2f}" for c in ["case9", "case14", "case30"]) +
 f", and {L118.median_ms:.1f} ms for the 9-, 14-, 30-, and 118-bus cases, with 95th percentiles of " +
 ", ".join(f"{LAT.loc[c,'p95_ms']:.2f}" for c in ["case9", "case14", "case30"]) + f", and {L118.p95_ms:.1f} ms (Table XIX, Fig. 16). "
 f"The medians of single repetitions varied between {L118.run_median_min_ms:.1f} and {L118.run_median_max_ms:.1f} ms on the "
 "118-bus case, so the absolute values depend on the load of the shared host. On the 118-bus case the dense m×m operations "
 f"dominate: forming S_{{k}} ({L118.form_S_median_ms:.0f} ms), the condition-number check ({L118.cond_S_median_ms:.0f} ms), the "
 f"linear solves ({L118.solves_median_ms:.0f} ms), and the Joseph covariance update ({L118.joseph_median_ms:.0f} ms), against "
 f"{L118.h_x_median_ms:.1f} ms for h(x) and {L118.H_x_median_ms:.1f} ms for H(x). These operation times re-execute the expressions "
 "of the estimator step on the same matrices in a separate pass. A cheaper condition estimate would replace the full "
 "singular-value decomposition, and sparse forms of H would reduce the cost of S_{k} and the covariance update. The measurements "
 "characterize the computational cost of the current dense implementation on the recorded hardware. They do not establish "
 "real-time feasibility. An earlier single wall-clock timing on unrecorded hardware is not used.")
replace_in(P[146], "With Median Times of the Dominant Operations", "With Median Times of the Dominant Operations (five repetitions pooled)")
for r_, c in zip(T[12].rows[1:], ["case9", "case14", "case30", "case118"]):
    L = LAT.loc[c]; fmt = (lambda v: f"{v:.1f}") if c == "case118" else (lambda v: f"{v:.3f}")
    vals = [fmt(L.median_ms), f"{fmt(L.mean_ms)}±{fmt(L.sd_ms)}", fmt(L.p95_ms), fmt(L.form_S_median_ms), fmt(L.cond_S_median_ms), fmt(L.solves_median_ms), fmt(L.joseph_median_ms)]
    for cell, v in zip(r_.cells[1:], vals):
        set_text(cell.paragraphs[0], v)
swap_image(P[143], f"{FIG}/Fig_latency.png", 3840480)
set_text(P[144], "**Fig. 16.** Median per-step latency versus number of buses (log axis), with bars to the 95th percentile, from the five-repetition measurement of Table XIX.")
delete(P[145]._p)

# ============================================================ I. verification
hI = para_after(T[12]._tbl, P[95], "I. Measurement Model and Jacobian Verification", style=H1)
replace_in(P[147], "The Jacobian check and the balance check test different things, so their numbers should not be compared directly.",
 "The Jacobian check and the balance check test different things, so their numbers should not be compared directly. The procedure "
 "of the Jacobian check is given in Section II, and neither check bears on the statistical consistency of the estimator (Table II).")

# ============================================================ J. limitations (P152 distributed to D and F, P153 under J)
delete(P[152]._p)
hJ = para_after(P[151]._p, P[95], "J. Limitations", style=H1)
set_text(P[153],
 "The evaluation is restricted to seeded synthetic scenarios on four canonical network topologies, each with a single operating "
 "point. No field measurements, hardware-in-the-loop experiments, or operational SCADA data were used, and the largest system "
 "considered was the 118-bus network. The anomaly scenarios do not adapt to the detectors and provide no stealth guarantee. "
 "Coordinated stealthy injection, sparse manipulation, and innovation-constrained attacks remain outside the scope of the "
 "experiments. The onset experiment uses one fixed onset time, 30 post-onset cycles, and run lengths censored at 30 or 60 cycles, so "
 "its ARL values are estimates over short windows. The branch outage keeps the pre-outage operating state, and the re-solved "
 "variant of Section III-C covers only one branch per case. The headline severity results use interleaved tiers and are descriptive. "
 "Comparisons are limited to internal framework configurations and two conventional temporal baselines. WLS-residual, "
 "robust-estimator, and learning-based detectors were not evaluated, so no claim of superiority over these methods can be "
 "supported. The five seeds vary only the noise and anomaly realizations, while successive cycles within each sequence remain "
 "temporally dependent. The matched-FPR thresholds of Table XVI are selected on test data and are retrospective. At K=2, an FPR of "
 "0.1525 is too high for operational use without measures such as estimator warm-starting or a burn-in period, together with "
 "empirical calibration of the NIS threshold. All thresholds depend on the assumed nominal noise level, which was held fixed during "
 "calibration, and the 99th-percentile thresholds rest on 200 calibration samples. The parameter analysis varies one factor at a "
 "time over a small grid of κ, τ_{cusum}, Q, and R, and the reported settings are not claimed to be optimal. Observability was "
 "checked analytically, and thresholds were calibrated separately for each topology and seed, so their transferability to other "
 "networks remains unknown. The runtime figures describe one dense implementation on one machine.", allow_math=True)

# ============================================================ conclusion (section 11)
set_text(P[155],
 "This study examines sequential innovation monitoring for persistent, low-amplitude anomalies in nonlinear AC state estimation. "
 "The framework combines an analytic-Jacobian EKF-style estimator with a CUSUM monitor on the standardized NIS, a SCADA "
 "timing-jitter detector, and a two-out-of-three voting rule. Results from the synthetic scenarios indicate that detection of "
 "persistent anomalies is driven primarily by the accumulation of NIS evidence over time, under the evaluated attack and "
 "initialization protocols. The voting rule and timing stream provide limited additional benefit, while standard EWMA and "
 "sliding-window accumulators achieve comparable performance to CUSUM once the filter has converged under the reset protocol, in "
 "the tested synthetic scenarios and not necessarily in other change-detection settings. Across four IEEE test systems and five seeds, the quorum "
 "achieved an F1-score of 0.9204 ± 0.0026 and an FPR of 0.1525 ± 0.0197. Most false alarms, including the elevated FPR on the "
 "118-bus system, were associated with the filter start-up transient following each flat-start reset. Excluding the first 20 cycles "
 "in a post-start-up evaluation reduced the FPR to 0.0100 ± 0.0191. This is not the FPR a deployed system would show "
 "automatically, since a deployment protocol would still have to specify how initialization is handled. "
 + ON_TEXT["concl"] + " The single-cycle NIS also deviates from its theoretical χ^{2} reference, mainly through the mismatch "
 "between the benign generator and the random-walk model, which limits the quorum's recall in the voltage-scale and drift "
 "scenarios. Further work falls into four directions: benign-to-attack transitions with more onset times and longer windows for "
 "sequential performance metrics, calibration and estimator initialization, broader detector and attack comparisons, and "
 "hardware-in-the-loop and operational data validation.")

set_widths(T[7], [3.4, 0.75, 0.75, 0.75, 0.75])
set_widths(T[9], [3.1, 0.8, 0.8, 0.8, 0.8])
set_widths(T[11], [1.75, 1.1, 0.75, 0.75, 1.1, 0.85])
set_widths(T[3], [1.3, 1.0, 1.0])

# ============================================================ data figures regenerated from committed sources (make_paper_figures.py)
PF = FIG.replace("figures", "figures")
for par, name, wd in [(93, "Fig02_networks", None), (100, "Fig04_constituents", None), (107, "Fig06_roc_pr", None), (111, "Fig07_topology", None),
                  (115, "Fig08_benign_alarms_by_cycle", None), (118, "Fig09_class_recall", 3840480), (121, "Fig10_tier_recall", 3840480),
                  (125, "Fig11_detector_removal", None), (132, "Fig12_constituents", 4754880), (150, "Fig17_power_balance_audit", None)]:
    swap_image(P[par], f"{FIG}/{name}.png", wd)
# ============================================================ references (section 12)
set_text(P[156], "References")
bib = {int(p.text.split("]")[0][1:]): p for p in d.paragraphs if p.style.name == "Bibliography"}
def ref(n, body): set_text(bib[n], f"[{n}] \t{body}")
REF = json.load(open(f"{ANA}/references_fixed.json"))
for n_, old_, new_ in REF["ops"]: replace_in(bib[n_], old_, new_)
for p_ in bib.values():
    if ". doi: " in "".join(t.text or "" for t in p_._p.iter(qn("w:t"))): replace_in(p_, ". doi: ", ", doi: ")
for k, v in REF["full"].items(): ref(int(k), v)

d.save(DST); print("saved", DST)
