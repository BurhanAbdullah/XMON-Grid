#!/usr/bin/env python3
"""Central finite-difference check of the analytic measurement Jacobian (Section II, Section III-I).

For each case one operating point is drawn with numpy.random.RandomState(2026), reseeded per case:
theta_2..theta_N ~ N(0, 0.05^2) rad, V_1..V_N ~ N(1, 0.02^2) p.u. Every state variable is perturbed by
+/- eps, eps = 1e-6 (no variable scaling); the central difference of h(x) over all 3N measurement channels
gives the numerical Jacobian (reference angle theta_1 not in the state, as in core.grid_topology).
Reported: largest absolute entry difference and relative Frobenius norm ||H - H_FD||_F / ||H||_F.
Usage: python jacobian_fd_check.py <repo_root> <out_csv>
"""
import sys, os, csv
REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO)
import numpy as np
from core.grid_topology import get_ieee_case_data, build_ybus, compute_h_x, compute_jacobian_H
rows = []
for c in ["case9", "case14", "case30", "case118"]:
    cd = get_ieee_case_data(c); _, G, B = build_ybus(cd); n = int(cd["num_buses"])
    rng = np.random.RandomState(2026)
    x = np.concatenate([rng.normal(0, 0.05, n - 1), rng.normal(1, 0.02, n)])
    H = compute_jacobian_H(x, G, B); eps = 1e-6; Hn = np.zeros_like(H)
    for j in range(x.size):
        e = np.zeros(x.size); e[j] = eps
        Hn[:, j] = (compute_h_x(x + e, G, B) - compute_h_x(x - e, G, B)) / (2 * eps)
    rows.append(dict(case=c, rows=H.shape[0], cols=H.shape[1], max_abs_err=float(np.max(np.abs(H - Hn))),
                     rel_frobenius=float(np.linalg.norm(H - Hn) / np.linalg.norm(H))))
    print(rows[-1])
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
