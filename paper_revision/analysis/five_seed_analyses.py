"""Analyses from the regenerated five-seed trace (repository protocol, verified identical to the repo run)."""
import sys, numpy as np, pandas as pd
from sklearn.metrics import matthews_corrcoef
SRC, OUT = sys.argv[1], sys.argv[2]
d = pd.read_csv(SRC)
def met(y, p):
    tp=int(((y==1)&(p==1)).sum()); fn=int(((y==1)&(p==0)).sum()); fp=int(((y==0)&(p==1)).sum()); tn=int(((y==0)&(p==0)).sum())
    pr=tp/(tp+fp) if tp+fp else 0; rc=tp/(tp+fn) if tp+fn else 0
    return dict(Precision=pr,Recall=rc,F1=2*pr*rc/(pr+rc) if pr+rc else 0,FPR=fp/(fp+tn) if fp+tn else 0,
                MCC=matthews_corrcoef(y,p) if len(set(p))>1 else 0, Accuracy=(tp+tn)/len(y))
# Issue 6: K=1 and K=2 on the same five-seed basis
rows=[]
for col in ['d_k1','d_k2']:
    per=pd.DataFrame([met(g.y_true.values,g[col].values)|{'seed':s} for s,g in d.groupby('seed')])
    per.assign(rule=col).to_csv(f'{OUT}/perseed_{col}.csv',index=False)
    rows.append({'rule':col,**{f'{m}_mean':per[m].mean() for m in ['Precision','Recall','F1','FPR','MCC','Accuracy']},
                 **{f'{m}_sd':per[m].std(ddof=1) for m in ['Precision','Recall','F1','FPR','MCC','Accuracy']}})
pd.DataFrame(rows).to_csv(f'{OUT}/T_k1_k2_5seed.csv',index=False)
# Issue 8: sequence-level false alarms of K=2 on benign sequences (one benign sequence per case and seed)
b=d[d.y_true==0].sort_values(['case','seed','sample_idx'])
rows=[]
for (c,s),g in b.groupby(['case','seed']):
    a=g.d_k2.values; k=g.sample_idx.values
    runs=[];cur=0
    for v in a:
        cur=cur+1 if v else 0; runs.append(cur)
    # count alarm runs (maximal consecutive alarm segments)
    nruns=int(((a[1:]==1)&(a[:-1]==0)).sum()+(a[0]==1))
    rows.append(dict(case=c,seed=s,any_alarm=int(a.any()),alarms=int(a.sum()),n_runs=nruns,longest_run=max(runs),
                     onset=int(k[a==1][0]) if a.any() else -1, startup_alarms=int(a[k<20].sum()),post_alarms=int(a[k>=20].sum()),
                     startup_any=int(a[k<20].any()),post_any=int(a[k>=20].any())))
sq=pd.DataFrame(rows); sq.to_csv(f'{OUT}/seq_false_alarms_k2.csv',index=False)
agg=sq.groupby('case').agg(seqs_alarmed=('any_alarm','sum'),startup_seqs=('startup_any','sum'),post_seqs=('post_any','sum'),
     longest=('longest_run','max'),runs_total=('n_runs','sum'),onset_min=('onset',lambda x: x[x>=0].min() if (x>=0).any() else -1),
     onset_max=('onset','max'),startup_alarms=('startup_alarms','sum'),post_alarms=('post_alarms','sum'),alarms=('alarms','sum'))
agg.to_csv(f'{OUT}/T_seq_false_alarms_k2.csv'); print(agg)
# Issue 9: five-seed recall by attack class for K=2, NIS, sequential monitor, leaky accumulator
a=d[d.y_true==1]
cl=a.groupby(['scenario','seed'])[['d_k2','a_nis','a_cusum','a_seq']].mean().groupby('scenario').agg(['mean','std'])
cl.to_csv(f'{OUT}/T_class_recall_5seed.csv'); print(cl.round(4))
# Issue 34: tau_comp variability across seeds
tc=d.groupby(['case','seed']).tau_comp.first().unstack(); tc.to_csv(f'{OUT}/tau_comp_by_seed.csv'); print(tc.round(4))
print(pd.read_csv(f'{OUT}/T_k1_k2_5seed.csv').T)

# Table XI: the three pairwise rules not in the original table (computed from the same frozen trace)
d['k'] = d.sample_idx
def met3(y, p):
    y = np.asarray(y); p = np.asarray(p); tp = ((y == 1) & (p == 1)).sum(); fn = ((y == 1) & (p == 0)).sum(); fp = ((y == 0) & (p == 1)).sum(); tn = ((y == 0) & (p == 0)).sum()
    pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    return dict(F1=2 * pr * rc / (pr + rc) if pr + rc else 0, Recall=rc, FPR=fp / (fp + tn) if fp + tn else 0)
rows = []
for lab, col in {'NIS OR jitter': d.a_nis | d.a_jitter, 'NIS AND jitter': d.a_nis & d.a_jitter, 'gk AND jitter': d.a_cusum & d.a_jitter}.items():
    d['_r'] = col.astype(int)
    a = pd.DataFrame([met3(g.y_true, g._r) for _, g in d.groupby('seed')]); b = pd.DataFrame([met3(g.y_true, g._r) for _, g in d[d.k >= 20].groupby('seed')])
    rows.append(dict(rule=lab, **{m: a[m].mean() for m in a}, **{m + '_sd': a[m].std(ddof=1) for m in a},
                     **{m + '_k20': b[m].mean() for m in b}, **{m + '_k20_sd': b[m].std(ddof=1) for m in b}))
pd.DataFrame(rows).to_csv(f'{OUT}/T_pairwise_rules.csv', index=False)
# Section III-D: configuration F with each case's own tau_comp, primary seed
p = d[d.seed == 2026]
pd.DataFrame([dict(rule='S_comp > per-case tau_comp, primary seed', **met3(p.y_true, (p.s_comp > p.tau_comp).astype(int)))]).to_csv(f'{OUT}/T_config_F_per_case_primary.csv', index=False)
