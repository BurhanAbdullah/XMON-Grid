# Final Paper Artifact Provenance

## Frozen quantitative sources

Figures 7, 8, and 12 are generated directly from the frozen verification package:

- `ablation_results.csv` — Figure 7
- `comparative_results.csv` — Figure 8
- `current_physical_sanity.csv` — Figure 12
- `multi_seed_summary.csv` — manuscript Table I and five-seed summary

The five-seed sample means and sample standard deviations reproduce the manuscript values:

- Accuracy: 0.8775 +/- 0.0042
- Precision: 0.9587 +/- 0.0051
- Recall: 0.8850 +/- 0.0012
- F1: 0.9204 +/- 0.0026
- FPR: 0.1525 +/- 0.0197
- MCC: 0.6667 +/- 0.0151

The physical audit maxima in the frozen CSV are:

- max |hP error| = 3.0905e-14 p.u.
- max |hQ error| = 2.4616e-14 p.u.
- max |power-balance residual| = 2.0428e-14 p.u.

## Current-validation figure sources

Figures 1--6 and Figures 9--11 use the current validation outputs under `results/independent_validation_run/`. They must be regenerated after the clean validation run and copied into this directory before the final submission tag. They are not declared frozen merely because an older copy exists elsewhere in the repository.

In particular, Figure 11 is exploratory unless the current timing experiment is regenerated and retained with the same provenance as the five-seed validation.

## Scientific rule

Figure layout, marker separation, legend placement, typography, and colour choices may be changed for readability. Numerical values, coordinates, thresholds, data selection, or statistical claims must not be changed solely to improve visual appearance.
