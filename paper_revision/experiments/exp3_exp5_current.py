#!/usr/bin/env python3
"""Experiments 3 and 5 of scripts/run_phase5e_robustness.py, logic copied verbatim, run on the current core (3bf598b).
Metrics: K=2 F1, recall, FPR over the 300 test cycles processed as one sequence (no per-scenario reset), as in the repository script.
Usage: python exp3_exp5_current.py <repo_root> <out_dir>"""
import sys, os, csv
REPO, OUT = sys.argv[1], sys.argv[2]; sys.path.insert(0, REPO); os.chdir(REPO)
import numpy as np
from core.xmon_model import XMONGridModel
from core.data_pipeline import generate_physical_dataset
def met(y, p):
    y=np.asarray(y); p=np.asarray(p); tp=int(((y==1)&(p==1)).sum()); fn=int(((y==1)&(p==0)).sum()); fp=int(((y==0)&(p==1)).sum()); tn=int(((y==0)&(p==0)).sum())
    pr=tp/(tp+fp) if tp+fp else 0; rc=tp/(tp+fn) if tp+fn else 0
    return dict(TP=tp,FN=fn,FP=fp,TN=tn,Recall=rc,F1=2*pr*rc/(pr+rc) if pr+rc else 0,FPR=fp/(fp+tn) if fp+tn else 0)
rows=[]
for s in [2026, 2027]:
    for c in ["case9", "case14"]:
        for n_cal in [50, 100, 200, 400]:
            model = XMONGridModel(case_name=c)
            data = generate_physical_dataset(case_name=c, num_calibration=n_cal, seed=s)
            model.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"]); model.reset()
            out = [model.step(z, dt) for z, dt in zip(data["test"]["z"], data["test"]["iat"])]
            rows.append(dict(experiment="Exp3", seed=s, case=c, param=n_cal, tau_comp=model.tau_comp, **met(data["test"]["labels"], [r["d_k2"] for r in out])))
for s in [2026, 2027]:
    c = "case9"
    for noise_scale in [0.0005, 0.001, 0.002, 0.005, 0.010]:
        model = XMONGridModel(case_name=c)
        data = generate_physical_dataset(case_name=c, seed=s)
        model.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"]); model.reset()
        tz = data["test"]["z"] + np.random.RandomState(s).normal(0, noise_scale, size=data["test"]["z"].shape)
        out = [model.step(z, dt) for z, dt in zip(tz, data["test"]["iat"])]
        rows.append(dict(experiment="Exp5", seed=s, case=c, param=noise_scale, tau_comp=model.tau_comp, **met(data["test"]["labels"], [r["d_k2"] for r in out])))
with open(f"{OUT}/exp3_exp5_current.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
