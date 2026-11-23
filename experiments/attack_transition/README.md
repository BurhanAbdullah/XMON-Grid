# Attack-transition experiment

This experiment supplements the reset-per-scenario benchmark by preserving the estimator
and detector state across a benign-to-attack transition.

## Protocol
- 200 benign calibration samples, followed by model reset.
- 50 benign test cycles, then 50 attacked cycles, without a reset at attack onset.
- One transition sequence per IEEE case, seed, and anomaly scenario.
- Fully benign 60-cycle controls are also recorded.
- Detectors recorded: NIS, CUSUM, timing, K=2 quorum, and leaky accumulator.
- The generator's measurement samples are independently drawn. Concatenating them creates
  a continuous detector/estimator state protocol, but not a temporally correlated SCADA
  process model. Interpret results accordingly.

## Run
From repository root:
```bash
python experiments/attack_transition/run_attack_transition.py
```

Outputs are written to `results/attack_transition/`.

This is an exploratory transition protocol. Detection delay and false-alarm metrics should
not be treated as operational estimates until the benign process model and sequence-level
statistical design are strengthened.
