#!/usr/bin/env python3
"""Repeated per-step latency of XMONGridModel.step (Table XIX, Fig. 16).

Protocol: five repetitions; in each, for each case, calibrate on the seed-2026 benign calibration samples (repository method), reset,
run 5 untimed warm-up steps, then time XMONGridModel.step with time.perf_counter over 300 consecutive
test cycles (60 for the 118-bus case) from a 305-cycle seed-2026 test block. Run with single-threaded BLAS (OPENBLAS_NUM_THREADS=1 etc.).

Component times (second pass, after a fresh reset and the same warm-up): before each step, x_pred and P_pred are
taken from estimator.predict() (side-effect free) and the dominant dense operations of PowerSystemStateEstimator.step are re-executed on those same
matrices with the same expressions (h(x), H(x), forming S_k, cond(S_k), the two linear solves, and the
Joseph covariance update). They never run inside the end-to-end timing pass. Statistics pool the timed steps of all five repetitions;
the range of the five per-repetition medians is also reported.
Usage: OPENBLAS_NUM_THREADS=1 python latency_repeated.py <repo_root> <out_dir>
"""
import sys, os, time, csv, platform, subprocess
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO); os.chdir(REPO); os.makedirs(OUT, exist_ok=True)
import numpy as np
from core.xmon_model import XMONGridModel
from core.data_pipeline import generate_physical_dataset
from core.grid_topology import compute_h_x, compute_jacobian_H

def T(f):
    t0 = time.perf_counter(); r = f(); return (time.perf_counter() - t0) * 1e3, r

REPS = 5
rows, raw = [], []
for case, n_timed in [("case9", 300), ("case14", 300), ("case30", 300), ("case118", 60)]:
    data = generate_physical_dataset(case_name=case, num_test_per_scenario=61, seed=2026)  # 305 cycles: 5 warm-up + 300 timed
    Z, D = data["test"]["z"], data["test"]["iat"]
    tot_all, run_medians = [], []
    comp = {k: [] for k in ["h_x", "H_x", "form_S", "cond_S", "solves", "joseph"]}
    for rep in range(REPS):
        m = XMONGridModel(case_name=case)
        m.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"]); m.reset()
        # pass 1: end-to-end XMONGridModel.step only (nothing else runs between timed calls)
        for i in range(5):
            m.step(Z[i], D[i])
        tot = []
        for j in range(5, 5 + n_timed):
            t0 = time.perf_counter(); m.step(Z[j], D[j]); tot.append((time.perf_counter() - t0) * 1e3)
        tot_all += tot; run_medians.append(float(np.median(tot)))
        raw += [dict(case=case, rep=rep, step=k, step_ms=v) for k, v in enumerate(tot)]
        # pass 2: component times on the same sequence after a fresh reset and the same warm-up
        m.reset()
        for i in range(5):
            m.step(Z[i], D[i])
        est = m.estimator
        for j in range(5, 5 + n_timed):
            x_pred, P_pred = est.predict()
            t_h, _ = T(lambda: compute_h_x(x_pred, est.G, est.B))
            t_H, H = T(lambda: compute_jacobian_H(x_pred, est.G, est.B))
            t_S, S = T(lambda: H @ P_pred @ H.T + est.R)
            S = 0.5 * (S + S.T)
            t_c, _ = T(lambda: float(np.linalg.cond(S)))
            r = Z[j] - compute_h_x(x_pred, est.G, est.B)
            t_s, K = T(lambda: (np.linalg.solve(S, r), np.linalg.solve(S.T, H @ P_pred).T)[1])
            t_j, _ = T(lambda: (lambda IKH: IKH @ P_pred @ IKH.T + K @ est.R @ K.T)(np.eye(est.state_dim) - K @ H))
            for k, v in zip(comp, [t_h, t_H, t_S, t_c, t_s, t_j]):
                comp[k].append(v)
            m.step(Z[j], D[j])
    tot = np.array(tot_all)
    rows.append(dict(case=case, buses=int(m.estimator.N), timed_steps_per_rep=n_timed, reps=REPS, median_ms=np.median(tot),
                     mean_ms=tot.mean(), sd_ms=tot.std(ddof=1), p95_ms=np.percentile(tot, 95),
                     run_median_min_ms=min(run_medians), run_median_max_ms=max(run_medians),
                     **{f"{k}_median_ms": float(np.median(v)) for k, v in comp.items()}))
    print(rows[-1], flush=True)
cpu = subprocess.run("lscpu | grep 'Model name'", shell=True, capture_output=True, text=True).stdout.split(":")[-1].strip()
mem = subprocess.run("free -g | awk '/Mem:/{print $2}'", shell=True, capture_output=True, text=True).stdout.strip()
hw = dict(cpu=cpu, logical_cpus=os.cpu_count(), ram_gb=mem, os=platform.platform(), python=platform.python_version(),
          numpy=np.__version__, openblas_threads=os.environ.get("OPENBLAS_NUM_THREADS", "unset"))
for name, rr in [("latency_repeated", rows), ("latency_steps_raw", raw), ("latency_hardware", [hw])]:
    with open(f"{OUT}/{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rr[0].keys()); w.writeheader(); w.writerows(rr)
print(hw)
