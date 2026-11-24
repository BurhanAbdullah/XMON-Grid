"""Recomputes manuscript Tables VIII, XI and XVI from the frozen five-seed trace.
Usage: python verify_manuscript_tables.py <detector_outputs_5seed.csv>"""
import sys, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, matthews_corrcoef
d=pd.read_csv(sys.argv[1]); pd.set_option('display.width',220)
d['k']=d.sample_idx
def met(y,p):
    tp=((y==1)&(p==1)).sum(); fn=((y==1)&(p==0)).sum(); fp=((y==0)&(p==1)).sum(); tn=((y==0)&(p==0)).sum()
    pr=tp/(tp+fp) if tp+fp else 0; rc=tp/(tp+fn) if tp+fn else 0
    return dict(F1=2*pr*rc/(pr+rc) if pr+rc else 0, Recall=rc, FPR=fp/(fp+tn) if fp+tn else 0)
# Table VIII of the manuscript (five-seed K=2 by topology)
print('Table VIII');
for c,g in d.groupby('case'):
    per=pd.DataFrame([met(h.y_true.values,h.d_k2.values) for s,h in g.groupby('seed')])
    per20=pd.DataFrame([met(h.y_true.values,h.d_k2.values) for s,h in g[g.k>=20].groupby('seed')])
    print(c, {m:f"{per[m].mean():.4f}±{per[m].std(ddof=1):.4f}" for m in per}, 'FPR20', f"{per20.FPR.mean():.4f}±{per20.FPR.std(ddof=1):.4f}")
# Table XI of the manuscript (structure-preserving rules)
d['or_nc']=d.a_nis|d.a_cusum; d['and_nc']=d.a_nis&d.a_cusum; d['c_or_j']=d.a_cusum|d.a_jitter
d['k3']=(d.a_nis+d.a_cusum+d.a_jitter>=3).astype(int)
d['k2_inst']=((d.a_nis+d.a_cusum_inst+d.a_jitter)>=2).astype(int)
d['s_pc']=(d.s_comp>d.tau_comp).astype(int)
t9=d[d.case=='case9'].groupby('seed').tau_comp.first(); d['s_9']=(d.s_comp>d.seed.map(t9)).astype(int)
print('Table XI')
for col in ['a_nis','a_cusum','a_jitter','a_seq','or_nc','and_nc','c_or_j','d_k1','d_k2','k3','k2_inst','s_9','s_pc']:
    per=pd.DataFrame([met(h.y_true.values,h[col].values) for s,h in d.groupby('seed')])
    per20=pd.DataFrame([met(h.y_true.values,h[col].values) for s,h in d[d.k>=20].groupby('seed')])
    print(f"{col:9s}", ' '.join(f"{per[m].mean():.4f}±{per[m].std(ddof=1):.4f}" for m in ['F1','Recall','FPR']), '|', f"{per20.F1.mean():.4f}±{per20.F1.std(ddof=1):.4f} {per20.FPR.mean():.4f}±{per20.FPR.std(ddof=1):.4f}")
# Table XVI: NIS, g_k, Theta_k and S_comp rows (the EWMA and window rows need the calibration moments and are
# computed in analyze_original_runs.py -> T_table12_check.csv). Retrospective thresholds: smallest benign test value at
# or above the (1-f) quantile ('higher' method), per case and seed; recall averaged over case-seed pairs; AUC averaged
# over cases within a seed, then mean and SD over seeds.
print('Table XVI rows')
for col in ['nis','cusum_g','theta_seq','s_comp']:
    for sub,name in [(d,'all'),(d[d.k>=20],'k20')]:
        aucs=[]; r05=[]; r15=[]
        for (s,c),g in sub.groupby(['seed','case']):
            aucs.append(dict(seed=s,case=c,auc=roc_auc_score(g.y_true,g[col])))
            b=g[g.y_true==0][col]; a=g[g.y_true==1][col]
            r05.append((a>np.quantile(b,0.95,method='higher')).mean()); r15.append((a>np.quantile(b,0.85,method='higher')).mean())
        A=pd.DataFrame(aucs).groupby('seed').auc.mean()
        print(col,name,f"AUC {A.mean():.4f}±{A.std(ddof=1):.4f} rec05 {np.mean(r05):.4f} rec15 {np.mean(r15):.4f}")
