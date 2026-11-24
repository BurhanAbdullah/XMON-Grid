#!/usr/bin/env python3
"""Benign-to-attack onset experiment (review issues 1-4, 10, 15).

All measurements come from core.data_pipeline.generate_physical_dataset and all detector
values from core.xmon_model.XMONGridModel at repository commit 3bf598b, unmodified.

The generator draws every sample independently given (scenario, tier), and the tier of
test sample i of an attack block is SEVERITY_TIERS[i % 4]. A larger test block
(num_test_per_scenario=1680) therefore provides independent benign samples and, for each
attack class, independent single-tier samples (every fourth sample). The calibration
block is drawn first, so the 200 calibration samples equal those of the original protocol.

Per case and seed:
  1. model.calibrate_benign(...) on the 200 calibration samples (repository method).
  2. Every sequence: model.reset(); 30 benign warm-up cycles through model.estimator.step
     only (no detector update, nothing scored); then scored cycles through model.step,
     with no further reset.
  3. Threshold-calibration sequences: 4 x 60 scored benign cycles.
     Benign test sequences: 4 x 60 scored benign cycles.
     Onset sequences: one per attack class and tier (16), 30 scored benign cycles, then
     30 attacked cycles of that class and tier (onset at scored index 30).
Usage: python onset_experiment.py <repo_root> <out_csv> <case> [seeds...]
"""
import sys, os, csv
REPO, OUT, CASE = sys.argv[1], sys.argv[2], sys.argv[3]
SEEDS = [int(s) for s in sys.argv[4:]] or [2026, 2027, 2028, 2029, 2030]
sys.path.insert(0, REPO); os.chdir(REPO)
import numpy as np
from core.xmon_model import XMONGridModel
from core.data_pipeline import generate_physical_dataset, SEVERITY_TIERS

WARM, NCAL, NBEN, PRE, POST = 30, 4, 4, 30, 30
CLASSES = ["branch_outage", "fdia", "load_shift", "stealth_drift"]
NTEST = 1680  # benign samples needed: (4+4)*(30+60) + 16*(30+30) = 1680

rows = []
for seed in SEEDS:
    m = XMONGridModel(case_name=CASE)
    data = generate_physical_dataset(case_name=CASE, num_calibration=200, num_validation=100,
                                     num_test_per_scenario=NTEST, seed=seed)
    m.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"]); m.reset()
    Z, T, meta = data["test"]["z"], data["test"]["iat"], data["test"]["metadata"]
    blocks = {}
    for i, md in enumerate(meta):
        blocks.setdefault(md["scenario"], []).append(i)
    ben = iter(blocks["baseline"])
    tierpool = {(c, t): [i for i in blocks[c] if meta[i]["severity_tier"] == t] for c in CLASSES for t in SEVERITY_TIERS}

    def run(kind, sid, scored, cls="baseline", tier="Tier 0 (Benign)", onset=None):
        m.reset()
        for _ in range(WARM):
            i = next(ben); m.estimator.step(Z[i])
        for k, i in enumerate(scored):
            r = m.step(Z[i], T[i])
            rows.append(dict(seed=seed, case=CASE, kind=kind, seq=sid, cls=cls, tier=tier, k=k,
                             onset=-1 if onset is None else onset, y_true=int(onset is not None and k >= onset),
                             nis=r["nis"], nis_threshold=r["nis_threshold"], cusum_g=r["cusum_g"],
                             s_comp=r["s_comp"], theta_seq=r["theta_seq"], theta_threshold=r["theta_threshold"],
                             tau_comp=r["tau_comp"], jitter_bar=r["jitter_bar"],
                             a_nis=r["a_nis"], a_cusum=r["a_cusum"], a_cusum_inst=r["a_cusum_inst"],
                             a_jitter=r["a_jitter"], a_seq=r["a_seq"], d_k1=r["d_k1"], d_k2=r["d_k2"],
                             mu0=m.cusum_detector.baseline_mean, sd0=m.cusum_detector.baseline_std))

    for s in range(NCAL):
        run("calib", f"cal{s}", [next(ben) for _ in range(60)])
    for s in range(NBEN):
        run("benign", f"ben{s}", [next(ben) for _ in range(60)])
    for c in CLASSES:
        for t in SEVERITY_TIERS:
            att = tierpool[(c, t)][:POST]
            run("onset", f"{c}|{t}", [next(ben) for _ in range(PRE)] + att, cls=c, tier=t, onset=PRE)
    print(CASE, "seed", seed, "done", flush=True)

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print("wrote", OUT, len(rows))
