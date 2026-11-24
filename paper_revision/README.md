# Paper revision: scripts, raw outputs, tables and figures

This folder holds everything behind the revised manuscript *Sequential NIS Monitoring for Persistent Anomaly Detection in AC State Estimation* (revision of 23 November 2026). Every number in the paper comes from these scripts and outputs.

## Ground rules

- The detector, estimator, generator and topology code in `core/` is used **unchanged** from commit `3bf598b`. No script in this folder modifies `core/`.
- A baseline rerun of the repository protocol (`experiments/original_protocol_runs.py`, configuration `base`) reproduces the frozen five-seed trace `results/raw/detector_outputs_5seed.csv` exactly:
  - every alarm flag matches;
  - the maximum NIS difference is 0.0 (`results/tables/reproduction_check.csv`).
- Two scripts go beyond the repository protocol, and say so in their docstrings:
  - `variants_benign_outage.py` changes only the state process: a random-walk benign state for the NIS consistency check, and a re-solved post-outage state.
  - `latency_repeated.py` re-executes the dense operations of the estimator step on the same matrices to time them separately.

## Run

From the repository root:

```bash
pip install -r requirements.txt
bash paper_revision/run_all.sh            # analyses, tables and figures from the committed raw outputs
bash paper_revision/run_all.sh --rerun    # also regenerates every raw output (about 3 h on 2 cores)
```

Runtime numbers depend on the machine (see `results/raw/latency_hardware.csv`). Every other output is deterministic under the fixed seeds.

## Where each result comes from

| Manuscript item | Script | Output |
|---|---|---|
| Table V, Table VI, Fig. 5 (K=1 and K=2, five seeds) | `analysis/five_seed_analyses.py` | `results/tables/T_k1_k2_5seed.csv`, `perseed_d_k*.csv` |
| Table VIII (five-seed topology, FPR k≥20), Table XI, Table XVI (NIS, g_k, Θ_k, S_comp rows) | `analysis/verify_manuscript_tables.py` | `results/tables/log_verify_manuscript_tables.txt` |
| Table XVI (EWMA and window-sum rows) | `analysis/analyze_original_runs.py` | `results/tables/T_table12_check.csv` |
| Table XI, added pairwise rules | `analysis/five_seed_analyses.py` | `results/tables/T_pairwise_rules.csv` |
| Table IX (sequence-level false alarms) | `analysis/five_seed_analyses.py` | `results/tables/T_seq_false_alarms_k2.csv`, `seq_false_alarms_k2.csv` |
| Table X (recall by anomaly class) | `analysis/five_seed_analyses.py` | `results/tables/T_class_recall_5seed.csv` |
| Section III-D, configuration F with per-case τ_comp | `analysis/five_seed_analyses.py` | `results/tables/T_config_F_per_case_primary.csv` |
| Section II, τ_comp range across seeds | `analysis/five_seed_analyses.py` | `results/tables/tau_comp_by_seed.csv` |
| Table XII, Fig. 11 (exploratory detector removal) | repository `scripts/run_independent_validation.py` | `results/paper_final_verified_20260908/ablation_results.csv` |
| Table XIII, Figs. 4 and 12 (constituents, primary seed) | repository `scripts/run_independent_validation.py` | `results/paper_final_verified_20260908/comparative_results.csv` |
| Table XIV (benign NIS diagnostics) | `analysis/analyze_original_runs.py` | `results/tables/T_nis_diagnostics_check.csv` |
| Table XV (NIS threshold variants) | `experiments/original_protocol_runs.py`, `analysis/analyze_original_runs.py` | `results/tables/T_nis_threshold_variants.csv` |
| Section III-E (matched random-walk benign process) | `experiments/variants_benign_outage.py` | `results/tables/T_benign_process.csv` |
| Section III-C (re-solved post-outage state) | `experiments/variants_benign_outage.py` | `results/tables/T_outage_resolved.csv`, `T_outage_fixed_state.csv` |
| Table XVII, Fig. 13, Section III-F (onset experiment) | `experiments/onset_experiment.py`, `analysis/analyze_onset.py` | `results/tables/T_onset_*.csv` |
| Table XVIII, Section III-G (parameter sensitivity) | `experiments/original_protocol_runs.py`, `analysis/analyze_original_runs.py`, `analysis/analyze_onset.py` | `results/tables/T_param_sensitivity.csv`, `T_onset_kappa_tau.csv` |
| Fig. 14, Section III-G (noise stress test, calibration size) | `experiments/exp3_exp5_current.py` | `results/raw/exp3_exp5_current.csv` |
| Fig. 15 (τ_comp versus calibration size) | `experiments/original_protocol_runs.py` | `results/tables/calib_size_all.csv` |
| Table XIX, Fig. 16, Section III-H (runtime) | `experiments/latency_repeated.py` | `results/raw/latency_repeated.csv`, `latency_hardware.csv` |
| Sections II and III-I (Jacobian check) | `experiments/jacobian_fd_check.py` | `results/raw/jacobian_fd_check.csv` |
| Table XX, Fig. 17 (power-balance audit) | repository code | `results/paper_final_verified_20260908/current_physical_sanity.csv` |
| Figs. 2, 4, 6–12, 17 | `analysis/make_paper_figures.py` | `figures/Fig02_*` … `figures/Fig17_*` |
| Figs. 3, 5, 13–16 | `analysis/make_revision_figures.py` | `figures/Fig_*` (the editable timeline is `figures/Fig_timeline.drawio`) |

Every figure has the values it plots in `figures/source_data/`.

`manuscript_tools/` turns the analysis tables into manuscript text and applies the revision to the author's draft. It needs the author's Word file and is included so that each number in the text can be traced to its table.

## Notes

- `results/independent_validation_run/robustness_results.csv` was produced before the five core fixes that followed commit `131a921`. The manuscript no longer uses it. The current-code noise and calibration-size results are in `results/raw/exp3_exp5_current.csv`.
- The branch `experiment/attack-transition` holds a different, exploratory transition protocol: 50 + 50 cycles from a flat start, with interleaved tiers. The manuscript does not use it. The onset experiment reported in the paper is `experiments/onset_experiment.py`: a 30-cycle warm-up, then 30 + 30 cycles with one constant tier, and thresholds frozen on separate benign calibration sequences.
