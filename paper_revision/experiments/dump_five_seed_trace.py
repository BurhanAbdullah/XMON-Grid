import sys, os, csv
REPO = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "scripts"))
os.chdir(REPO)
import run_independent_validation as v
rows_all = []
for s in v.MULTI_SEEDS:
    rows, _ = v.run_experiment_seed(s)
    rows_all += rows
    print("seed", s, len(rows), flush=True)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows_all[0].keys()); w.writeheader(); w.writerows(rows_all)
print("wrote", OUT, len(rows_all))
