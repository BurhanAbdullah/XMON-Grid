#!/bin/bash
# Reproduces every result, table and figure of the revised manuscript from the repository code.
# Usage (from the repository root):
#   bash paper_revision/run_all.sh            # analyses, tables and figures from the committed raw outputs (minutes)
#   bash paper_revision/run_all.sh --rerun    # also regenerates every raw output from scratch (about 3 h on 2 cores)
set -euo pipefail
export PYTHONWARNINGS=ignore OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
REPO=$(git rev-parse --show-toplevel); PR=$REPO/paper_revision
RAW=$PR/results/raw; TAB=$PR/results/tables; FIG=$PR/figures
mkdir -p "$RAW" "$TAB" "$FIG"

if [[ "${1:-}" == "--rerun" ]]; then
  python3 "$PR/experiments/dump_five_seed_trace.py" "$REPO" "$RAW/detector_outputs_5seed.csv"   # frozen five-seed trace
  for c in case9 case14 case30 case118; do
    python3 "$PR/experiments/onset_experiment.py"       "$REPO" "$RAW/onset_$c.csv" "$c"   # Section III-F, Table XVII, Fig. 13
    python3 "$PR/experiments/original_protocol_runs.py" "$REPO" "$RAW" "$c"                # Tables XV, XVIII, Fig. 15
    python3 "$PR/experiments/variants_benign_outage.py" "$REPO" "$RAW" "$c"                # Sections III-C and III-E
  done
  python3 "$PR/experiments/exp3_exp5_current.py" "$REPO" "$RAW"                            # Section III-G, Fig. 14
  python3 "$PR/experiments/jacobian_fd_check.py"  "$REPO" "$RAW/jacobian_fd_check.csv"    # Sections II and III-I
  python3 "$PR/experiments/latency_repeated.py"   "$REPO" "$RAW"                           # Section III-H, Table XIX, Fig. 16
fi

TRACE=$RAW/detector_outputs_5seed.csv
python3 "$PR/analysis/five_seed_analyses.py" "$TRACE" "$TAB" > /dev/null
python3 "$PR/analysis/analyze_onset.py" "$TAB" "$RAW"/onset_case9.csv "$RAW"/onset_case14.csv "$RAW"/onset_case30.csv "$RAW"/onset_case118.csv > "$TAB/log_onset.txt"
python3 "$PR/analysis/analyze_original_runs.py" "$RAW" "$TAB" "$TRACE" > "$TAB/log_original.txt"
python3 "$PR/manuscript_tools/build_text.py" "$TAB" > "$TAB/log_text.txt"
python3 "$PR/analysis/verify_manuscript_tables.py" "$TRACE" > "$TAB/log_verify_manuscript_tables.txt"
python3 "$PR/analysis/make_revision_figures.py" "$TAB" "$RAW" "$FIG" > /dev/null
python3 "$PR/analysis/make_paper_figures.py" "$REPO" "$TRACE" "$FIG" > /dev/null
echo "done: tables in $TAB, figures in $FIG"
