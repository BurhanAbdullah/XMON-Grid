#!/usr/bin/env python3
"""Original-protocol runs with the repository code (review issues 15, 20, 34).

Loop identical to scripts/run_independent_validation.py::run_experiment_seed (per-scenario
reset, 200 calibration samples, 60 test samples per scenario). Configuration "base" uses the
repository Q and R and must reproduce the frozen trace. Configurations Qx0.1, Qx10, Rx0.5,
Rx2 multiply the estimator's process-noise covariance Q or assumed measurement covariance R
after construction and before calibration (the generated data are unchanged).
Also written: the 200 calibration NIS values per case and seed (same estimator steps as
calibrate_benign), and calibration quantities for calibration sizes 50/100/200/400.
Usage: python original_protocol_runs.py <repo_root> <out_dir> <case> [seeds...]
"""
import sys, os, csv
REPO, OUT, CASE = sys.argv[1], sys.argv[2], sys.argv[3]
SEEDS = [int(s) for s in sys.argv[4:]] or [2026, 2027, 2028, 2029, 2030]
sys.path.insert(0, REPO); os.chdir(REPO)
import numpy as np
from core.xmon_model import XMONGridModel, PowerSystemStateEstimator
from core.data_pipeline import generate_physical_dataset

CONFIGS = [("base", 1.0, 1.0), ("Qx0.1", 0.1, 1.0), ("Qx10", 10.0, 1.0), ("Rx0.5", 1.0, 0.5), ("Rx2", 1.0, 2.0)]
rows, cal_rows, size_rows = [], [], []
for seed in SEEDS:
    data = generate_physical_dataset(case_name=CASE, num_calibration=200, num_validation=100,
                                     num_test_per_scenario=60, seed=seed)
    # calibration NIS values (same as the nis_list inside calibrate_benign)
    est = PowerSystemStateEstimator(case_name=CASE)
    for j, z in enumerate(data["calibration"]["z"]):
        cal_rows.append(dict(seed=seed, case=CASE, j=j, nis=est.step(z)["nis"]))
    for cfg, qs, rs in CONFIGS:
        m = XMONGridModel(case_name=CASE)
        m.estimator.Q = m.estimator.Q * qs; m.estimator.R = m.estimator.R * rs
        m.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"]); m.reset()
        cur = None
        for z, t, y, md in zip(data["test"]["z"], data["test"]["iat"], data["test"]["labels"], data["test"]["metadata"]):
            if md["scenario"] != cur:
                cur = md["scenario"]; m.reset()
            r = m.step(z, t)
            rows.append(dict(cfg=cfg, seed=seed, case=CASE, scenario=cur, severity_tier=md["severity_tier"],
                             sample_idx=md["sample_idx"], y_true=int(y), nis=r["nis"], nis_threshold=r["nis_threshold"],
                             cusum_g=r["cusum_g"], a_nis=r["a_nis"], a_cusum=r["a_cusum"], a_jitter=r["a_jitter"],
                             a_seq=r["a_seq"], d_k2=r["d_k2"], d_k1=r["d_k1"], s_comp=r["s_comp"], tau_comp=r["tau_comp"],
                             mu0=m.cusum_detector.baseline_mean, sd0=m.cusum_detector.baseline_std))
    # calibration size: repository calibrate_benign on the first n of 400 benign calibration samples
    d4 = generate_physical_dataset(case_name=CASE, num_calibration=400, num_validation=100,
                                   num_test_per_scenario=60, seed=seed)
    for n in [50, 100, 200, 400]:
        m = XMONGridModel(case_name=CASE)
        m.calibrate_benign(d4["calibration"]["z"][:n], d4["calibration"]["iat"][:n])
        size_rows.append(dict(seed=seed, case=CASE, n=n, tau_comp=m.tau_comp,
                              tau_theta=m.sequential_accumulator.threshold,
                              mu0=m.cusum_detector.baseline_mean, sd0=m.cusum_detector.baseline_std))
    print(CASE, "seed", seed, "done", flush=True)

for name, rr in [("trace", rows), ("calib_nis", cal_rows), ("calib_size", size_rows)]:
    with open(f"{OUT}/{name}_{CASE}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rr[0].keys()); w.writeheader(); w.writerows(rr)
print("wrote", CASE)
