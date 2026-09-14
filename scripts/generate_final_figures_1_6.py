#!/usr/bin/env python3
"""Generate clean Figures 1--6 from the current validation outputs."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "independent_validation_run"
OUT = ROOT / "results" / "paper_final_verified_20260908" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.titlesize":12,"axes.labelsize":10,"xtick.labelsize":9,"ytick.labelsize":9,"legend.fontsize":9,"axes.grid":True,"grid.alpha":0.22,"grid.linestyle":"--","savefig.bbox":"tight"})

def rd(path):
    with path.open(newline="") as f: return list(csv.DictReader(f))
def save(fig, stem):
    fig.savefig(OUT/f"{stem}.pdf"); fig.savefig(OUT/f"{stem}.png", dpi=600); plt.close(fig)

def fig1():
    rows=rd(SRC/"metrics"/"detector_outputs.csv"); y=np.array([int(r["y_true"]) for r in rows])
    streams=[("NIS Standalone","a_nis"),("CUSUM Standalone","a_cusum"),("Jitter Standalone","a_jitter"),("Sequential Accumulator","a_seq")]
    preds=[(n,np.array([int(r[k]) for r in rows])) for n,k in streams]
    preds += [("XMON-Grid K=1",((preds[0][1]+preds[1][1]+preds[2][1])>=1).astype(int)),("XMON-Grid K=2",np.array([int(r["d_k2"]) for r in rows]))]
    vals=[]
    for n,p in preds:
        tp=((p==1)&(y==1)).sum(); fp=((p==1)&(y==0)).sum(); fn=((p==0)&(y==1)).sum(); tn=((p==0)&(y==0)).sum()
        rec=tp/(tp+fn); fpr=fp/(fp+tn); f1=2*tp/(2*tp+fp+fn); vals.append((n,f1,rec,fpr))
    x=np.arange(len(vals)); w=.25; fig,ax=plt.subplots(figsize=(8.5,4.6))
    for off,idx,label in [(-w,1,"F1-score"),(0,2,"Recall"),(w,3,"FPR")]: ax.bar(x+off,[v[idx] for v in vals],w,label=label)
    ax.set_ylabel("Metric value"); ax.set_ylim(0,1.08); ax.set_xticks(x); ax.set_xticklabels([v[0].replace(" ","\n") for v in vals]); ax.set_title("Fig. 1 — Overall Detection-Performance Comparison"); ax.legend(loc="upper right")
    fig.tight_layout(); save(fig,"fig1_overall_performance")

def fig2():
    rows=rd(ROOT/"results"/"paper_final_verified_20260908"/"comparative_results.csv"); d={r["Method"]:r for r in rows}
    k1=d["10. XMON-Grid K=1 (Sensitivity Mode)"]; k2=d["9. XMON-Grid K=2 (Strict Majority)"]
    pts=[("K=1",float(k1["FPR"]),float(k1["Recall"]),"s"),("K=2",float(k2["FPR"]),float(k2["Recall"]),"D")]
    fig,ax=plt.subplots(figsize=(6.8,4.4))
    for name,x,y,m in pts: ax.scatter(x,y,s=90,marker=m,edgecolor="black",linewidth=.8,label=name); ax.annotate(name,(x,y),xytext=(7,8),textcoords="offset points",fontweight="bold")
    ax.set_xlabel("False-positive rate (FPR)"); ax.set_ylabel("Recall (sensitivity)"); ax.set_title("Fig. 2 — K=1 vs. K=2 Operating-Point Trade-off"); ax.set_xlim(0,0.72); ax.set_ylim(.80,1.03); ax.legend(loc="lower left")
    fig.tight_layout(); save(fig,"fig2_k1_vs_k2_tradeoff")

def fig3():
    rows=rd(SRC/"metrics"/"detector_outputs.csv"); y=np.array([int(r["y_true"]) for r in rows]); s=np.array([float(r["s_comp"]) for r in rows]); f,t,_=roc_curve(y,s); a=auc(f,t)
    fig,ax=plt.subplots(figsize=(5.8,4.5)); ax.plot(f,t,lw=2,label=f"$S_{{comp}}$ (AUC={a:.4f})"); ax.plot([0,1],[0,1],"k--",lw=1,label="Random baseline"); ax.set_xlabel("False-positive rate"); ax.set_ylabel("True-positive rate"); ax.set_title("Fig. 3 — Receiver Operating Characteristic"); ax.legend(loc="lower right"); ax.set_xlim(0,1); ax.set_ylim(0,1.02); fig.tight_layout(); save(fig,"fig3_roc_curve")

def fig4():
    rows=rd(SRC/"metrics"/"detector_outputs.csv"); y=np.array([int(r["y_true"]) for r in rows]); s=np.array([float(r["s_comp"]) for r in rows]); p,r,_=precision_recall_curve(y,s); a=auc(r,p)
    fig,ax=plt.subplots(figsize=(5.8,4.5)); ax.plot(r,p,lw=2,label=f"$S_{{comp}}$ (PR-AUC={a:.4f})"); ax.set_xlabel("Recall (sensitivity)"); ax.set_ylabel("Precision"); ax.set_title("Fig. 4 — Precision–Recall Curve"); ax.set_xlim(0,1); ax.set_ylim(.70,1.02); ax.legend(loc="lower left"); fig.tight_layout(); save(fig,"fig4_pr_curve")

def fig5():
    rows=rd(SRC/"audit"/"audit_5seed_case_wise.csv"); labels=[r["case"].upper() for r in rows]; f=[float(r["mean_F1"]) for r in rows]; sd=[float(r["SD_F1"]) for r in rows]; x=np.arange(len(labels)); fig,ax=plt.subplots(figsize=(6.5,4.1)); ax.bar(x,f,yerr=sd,capsize=4,width=.55,edgecolor="black",linewidth=.5); ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(.80,1.04); ax.set_ylabel("Mean F1-score (5 seeds)"); ax.set_title("Fig. 5 — Case-Wise Performance"); fig.tight_layout(); save(fig,"fig5_casewise_performance")

def fig6():
    rows=[r for r in rd(SRC/"audit"/"audit_5seed_attack_wise.csv") if r["scenario"]!="baseline"]; labels=[r["scenario"].replace("_"," ").title() for r in rows]; f=[float(r["mean_F1"]) for r in rows]; rec=[float(r["mean_Recall"]) for r in rows]; x=np.arange(len(labels)); w=.36; fig,ax=plt.subplots(figsize=(7,4.1)); ax.bar(x-w/2,f,w,label="F1-score",edgecolor="black",linewidth=.5); ax.bar(x+w/2,rec,w,label="Recall",edgecolor="black",linewidth=.5); ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(.60,1.04); ax.set_ylabel("Metric value (5 seeds)"); ax.set_title("Fig. 6 — Attack-Wise Performance"); ax.legend(loc="lower left"); fig.tight_layout(); save(fig,"fig6_attackwise_performance")

if __name__=="__main__":
    for fn in (fig1,fig2,fig3,fig4,fig5,fig6): fn()
    print(f"Figures 1--6 written to {OUT}")
