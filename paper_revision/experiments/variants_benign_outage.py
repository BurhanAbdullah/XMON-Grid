#!/usr/bin/env python3
"""Generator variants for review issues 12 and 13. Detector, estimator, measurement function, noise levels and
calibration are the repository code (commit 3bf598b). Only the state process differs, as stated below.

Issue 13, matched benign process. Two benign generators, each used for its own calibration (200 samples, repository
calibrate_benign) and for five 60-cycle test sequences with a flat-start reset per sequence (original protocol):
  iid : repository generator, independent perturbation of the solved operating point every cycle
        (benign block of generate_physical_dataset).
  rw  : random walk x_k = x_{k-1} + w_k, w_k ~ N(0, Q) with the estimator's own Q, started at the solved operating
        point at the start of every sequence. Measurements: compute_h_x(x_k) plus the repository noise
        (0.002 p.u. on V, 0.005 p.u. on P/Q) and inter-arrival times N(0.004, 0.0005^2) clipped at 1e-4 s.
Issue 12, physically settled outage. The branch chosen by _select_outage_branch is switched off and the AC power flow is
  re-solved with PYPOWER. Samples use the post-outage solution x_post instead of the pre-outage state, with the
  repository tier-dependent state noise and the post-outage admittance matrix, cyclically interleaved tiers, one
  60-cycle sequence per case and seed after the repository calibration.
Usage: python variants_benign_outage.py <repo_root> <out_dir> <case> [seeds...]
"""
import sys, os, csv
from importlib import import_module
REPO, OUT, CASE = sys.argv[1], sys.argv[2], sys.argv[3]
SEEDS = [int(s) for s in sys.argv[4:]] or [2026, 2027, 2028, 2029, 2030]
sys.path.insert(0, REPO); os.chdir(REPO)
import numpy as np
from core.xmon_model import XMONGridModel
from core.data_pipeline import generate_physical_dataset, _nominal_state, _select_outage_branch, SEVERITY_TIERS
from core.grid_topology import get_ieee_case_data, build_ybus, compute_h_x
from pypower.api import ppoption, runpf

cd = get_ieee_case_data(CASE); n = int(cd["num_buses"]); _, G, B = build_ybus(cd); x_nom = _nominal_state(CASE)
idx, fb, tb = _select_outage_branch(cd)
oc = {**cd, "branch": np.asarray(cd["branch"], float).copy()}; oc["branch"][idx, 10] = 0.0; _, Go, Bo = build_ybus(oc)
mpc = getattr(import_module(f"pypower.{CASE}"), CASE)(); mpc["branch"][idx, 10] = 0
sol, ok = runpf(mpc, ppoption(VERBOSE=0, OUT_ALL=0)); assert ok, "post-outage power flow failed"
bus = np.asarray(sol["bus"], float); x_post = np.concatenate([np.deg2rad(bus[1:, 8]), bus[:, 7]])
TS = {"Tier 1 (Subtle)": (0.0015, 0.0025), "Tier 2 (Moderate)": (0.0030, 0.0050), "Tier 3 (Strong)": (0.0050, 0.0080), "Tier 4 (Severe)": (0.0080, 0.0120)}
rows = []
for seed in SEEDS:
    rng = np.random.RandomState(seed + 7919)
    noise = lambda: np.concatenate([rng.normal(0, 0.002, n), rng.normal(0, 0.005, 2 * n)])
    dt = lambda: max(0.0001, float(rng.normal(0.004, 0.0005)))
    data = generate_physical_dataset(case_name=CASE, num_calibration=200, num_validation=100, num_test_per_scenario=300, seed=seed)
    tmp = XMONGridModel(case_name=CASE); Qd = np.diag(tmp.estimator.Q).copy()
    def rw_seq(L):
        x = x_nom.copy(); zs = []
        for _ in range(L):
            x = x + rng.normal(0, np.sqrt(Qd)); zs.append((compute_h_x(x, G, B) + noise(), dt()))
        return zs
    gens = {"iid": ([(z, t) for z, t in zip(data["calibration"]["z"], data["calibration"]["iat"])],
                    [list(zip(data["test"]["z"][j * 60:(j + 1) * 60], data["test"]["iat"][j * 60:(j + 1) * 60])) for j in range(5)]),
            "rw": (rw_seq(200), [rw_seq(60) for _ in range(5)])}
    for gname, (cal, seqs) in gens.items():
        m = XMONGridModel(case_name=CASE)
        m.calibrate_benign(np.array([c[0] for c in cal]), np.array([c[1] for c in cal]))
        for j, s in enumerate(seqs):
            m.reset()
            for k, (z, t) in enumerate(s):
                r = m.step(z, t)
                rows.append(dict(exp="benign_process", gen=gname, seed=seed, case=CASE, seq=j, k=k, y_true=0, tier="",
                                 nis=r["nis"], nis_threshold=r["nis_threshold"], a_nis=r["a_nis"], a_cusum=r["a_cusum"], d_k2=r["d_k2"]))
    # Issue 12: re-solved post-outage state, repository calibration
    m = XMONGridModel(case_name=CASE); m.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"]); m.reset()
    for k in range(60):
        tier = SEVERITY_TIERS[k % 4]; sa, sv = TS[tier]
        x = x_post.copy(); x[:n - 1] += rng.normal(0, sa, n - 1); x[n - 1:] += rng.normal(0, sv, n)
        r = m.step(compute_h_x(x, Go, Bo) + noise(), dt())
        rows.append(dict(exp="outage_resolved", gen="post_pf", seed=seed, case=CASE, seq=0, k=k, y_true=1, tier=tier,
                         nis=r["nis"], nis_threshold=r["nis_threshold"], a_nis=r["a_nis"], a_cusum=r["a_cusum"], d_k2=r["d_k2"]))
    print(CASE, seed, "done", flush=True)
rows.append(dict(exp="meta", gen=f"branch {fb}-{tb}; max|V_post-V_pre|={np.max(np.abs(x_post[n-1:]-x_nom[n-1:])):.5f}; "
                 f"max|theta_post-theta_pre|={np.max(np.abs(x_post[:n-1]-x_nom[:n-1])):.5f}", seed=0, case=CASE, seq=0, k=0, y_true=0, tier="",
                 nis=0, nis_threshold=0, a_nis=0, a_cusum=0, d_k2=0))
with open(f"{OUT}/variants_{CASE}.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print("wrote", CASE)
