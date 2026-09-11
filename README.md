# XMON-Grid

## Sequential Innovation Accumulation and Cross-Layer Quorum Consensus for Topology-Attack Detection in SCADA-Monitored Transmission Systems

This repository contains the research implementation, benchmark generation code, validation tests, and manuscript source for XMON-Grid.

### Scientific scope

XMON-Grid combines three detector streams:

- normalized innovation squared (NIS) from the state-estimation model;
- a standardized one-sided CUSUM detector for residual drift;
- a telemetry timing-jitter detector.

The detector streams are combined by a strict majority quorum (`K=2`) and an optional sensitivity mode (`K=1`). The sequential accumulation statistic is retained as an auxiliary temporal detector and is evaluated separately; it is not silently counted as a fourth quorum vote.

### Benchmark provenance

The benchmark networks are the standard PYPOWER/MATPOWER IEEE 9-, 14-, 30-, and 118-bus cases. The network topology and electrical parameters are canonical benchmark data. Measurements, noise, and attack realizations are **synthetic and seeded**. They are not field SCADA measurements.

The five benchmark conditions are:

1. benign baseline;
2. canonical non-islanding branch outage;
3. synthetic false-data injection attack;
4. synthetic load-equivalent state perturbation;
5. synthetic slow state drift.

The distinction between canonical network data and synthetic measurement/attack generation is part of the reproducibility contract and is checked automatically.

### Validation status

The authoritative quantitative reference is the clean verification package in `results/paper_final_verified_20260908/`. It records the exact verification provenance, five-seed summary, ablation/comparative results, and physical sanity audit used for the manuscript.

The verification was performed from a clean source state and reported 20/20 unit tests, a five-seed / four-topology / 6,000-evaluation reproduction, and passing physical sanity checks. Historical directories such as `results/independent_validation_run/` and `results/tsg_run_002/` remain available only as historical evidence and must not be cited as the final regenerated result package.

A result is considered submission-ready only when it is traceable to the current source code, the canonical benchmark definition, the seed manifest, and a successful validation run. Figure files used by the manuscript must likewise be generated into `results/paper_final_verified_20260908/figures/` and checked by the final-artifact validation script.

### Reproduction

```bash
git clone https://github.com/BurhanAbdullah/XMON-Grid.git
cd XMON-Grid
pip install -r requirements.txt
python scripts/validate_canonical_benchmarks.py
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/run_independent_validation.py
python scripts/physical_sanity_check.py
python scripts/validate_paper_final_artifacts.py
```

The repository also pins the MATPOWER submodule through `.gitmodules`; the Python benchmark path uses PYPOWER directly so the core validation does not depend on a MATLAB/Octave installation.

### Repository structure

```text
core/                       authoritative model and benchmark generation
scripts/                    validation, reproduction and figure tooling
tests/                      automated unit tests
results/paper_final_verified_20260908/  frozen verification artifacts
paper/main.tex              manuscript source
archive/                    explicitly historical material
```

### Important scientific rule

No numerical claim, figure, table, speedup, physical-consistency value, or comparative result is considered submission-ready merely because it exists in an older result directory. It must be traceable to the current source code, current benchmark definition, current seed manifest, and a successful validation run. Visual cleanup must never alter the underlying data, coordinates, thresholds, or reported statistics.

## License

MIT License.
