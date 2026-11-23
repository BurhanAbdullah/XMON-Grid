#!/usr/bin/env python3
"""Attack-transition experiment for XMON-Grid.

A single estimator/detector run is maintained across the benign-to-attack transition.
This experiment supplements (does not replace) the reset-per-scenario benchmark.

Outputs:
  results/attack_transition/transition_sequences.csv
  results/attack_transition/summary.csv

The existing synthetic generator supplies independently sampled measurement vectors.
They are concatenated into a continuous estimator/detector stream; this is a
transition-protocol test, not a temporally correlated SCADA simulator.
"""
from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from statistics import mean, median

import numpy as np

from core.xmon_model import XMONGridModel
from core.data_pipeline import generate_physical_dataset

CASES = ("case9", "case14", "case30", "case118")
ATTACK_SCENARIOS = ("branch_outage", "fdia", "load_shift", "stealth_drift")
SEEDS = (2026, 2027, 2028, 2029, 2030)
PRE_ATTACK = 50
POST_ATTACK = 50


def first_true(values):
    for i, value in enumerate(values):
        if bool(value):
            return i
    return None


def summarize_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["case"], row["scenario"], row["detector"])].append(row)
    summary = []
    for (case, scenario, detector), group in sorted(groups.items()):
        detected = [r for r in group if r["detected"] == "1"]
        delays = [int(r["delay_cycles"]) for r in detected if r["delay_cycles"] != ""]
        summary.append({
            "case": case,
            "scenario": scenario,
            "detector": detector,
            "sequences": len(group),
            "detection_rate": len(detected) / len(group),
            "median_detection_delay_cycles": median(delays) if delays else "",
            "mean_detection_delay_cycles": mean(delays) if delays else "",
            "pre_attack_false_alarm_rate": sum(int(r["pre_attack_alarm"]) for r in group) / len(group),
        })
    return summary


def run(output_dir: str, seeds=SEEDS):
    os.makedirs(output_dir, exist_ok=True)
    sequence_rows = []
    for case in CASES:
        for seed in seeds:
            data = generate_physical_dataset(
                case_name=case, num_calibration=200, num_validation=100,
                num_test_per_scenario=60, seed=seed,
            )
            model = XMONGridModel(case_name=case)
            model.calibrate_benign(data["calibration"]["z"], data["calibration"]["iat"])

            # The generator groups test samples by scenario. Use baseline and each
            # attack block to form explicit 50+50 transitions without resets.
            z_base = np.asarray(data["test"]["z"][:60])
            iat_base = np.asarray(data["test"]["iat"][:60])
            labels = np.asarray(data["test"]["labels"])
            meta = data["test"]["metadata"]
            baseline_idx = [i for i, m in enumerate(meta) if m["scenario"] == "baseline"]
            if len(baseline_idx) < PRE_ATTACK:
                raise RuntimeError(f"Insufficient benign samples for {case}, seed={seed}")
            for scenario in ATTACK_SCENARIOS:
                attack_idx = [i for i, m in enumerate(meta) if m["scenario"] == scenario]
                if len(attack_idx) < POST_ATTACK:
                    raise RuntimeError(f"Insufficient {scenario} samples for {case}, seed={seed}")
                pre = baseline_idx[:PRE_ATTACK]
                post = attack_idx[:POST_ATTACK]
                stream_idx = pre + post
                model.reset()
                trace = []
                for idx in stream_idx:
                    step = model.step(data["test"]["z"][idx], data["test"]["iat"][idx])
                    trace.append(step)
                alarm_map = {
                    "NIS": [int(x["a_nis"]) for x in trace],
                    "CUSUM": [int(x["a_cusum"]) for x in trace],
                    "Timing": [int(x["a_jitter"]) for x in trace],
                    "K2_quorum": [int(x["d_k2"]) for x in trace],
                    "Leaky_accumulator": [int(x["a_seq"]) for x in trace],
                }
                for detector, alarms in alarm_map.items():
                    pre_alarm = first_true(alarms[:PRE_ATTACK])
                    attack_alarm = first_true(alarms[PRE_ATTACK:])
                    delay = (attack_alarm if attack_alarm is not None else "")
                    sequence_rows.append({
                        "case": case, "seed": seed, "scenario": scenario,
                        "detector": detector,
                        "pre_attack_alarm": int(pre_alarm is not None),
                        "pre_attack_alarm_cycle": pre_alarm if pre_alarm is not None else "",
                        "detected": int(attack_alarm is not None),
                        "delay_cycles": delay,
                        "alarm_cycle_absolute": (PRE_ATTACK + attack_alarm) if attack_alarm is not None else "",
                    })
            # Fully benign control: no attack transition, one continuous run.
            model.reset()
            benign_trace = []
            for idx in baseline_idx[:60]:
                benign_trace.append(model.step(data["test"]["z"][idx], data["test"]["iat"][idx]))
            for detector, alarms in {
                "NIS": [int(x["a_nis"]) for x in benign_trace],
                "CUSUM": [int(x["a_cusum"]) for x in benign_trace],
                "Timing": [int(x["a_jitter"]) for x in benign_trace],
                "K2_quorum": [int(x["d_k2"]) for x in benign_trace],
                "Leaky_accumulator": [int(x["a_seq"]) for x in benign_trace],
            }.items():
                first_alarm = first_true(alarms)
                sequence_rows.append({
                    "case": case, "seed": seed, "scenario": "fully_benign",
                    "detector": detector, "pre_attack_alarm": int(first_alarm is not None),
                    "pre_attack_alarm_cycle": first_alarm if first_alarm is not None else "",
                    "detected": "", "delay_cycles": "",
                    "alarm_cycle_absolute": first_alarm if first_alarm is not None else "",
                })

    sequence_path = os.path.join(output_dir, "transition_sequences.csv")
    with open(sequence_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sequence_rows[0]))
        writer.writeheader()
        writer.writerows(sequence_rows)

    transition_only = [r for r in sequence_rows if r["scenario"] != "fully_benign"]
    summary = summarize_rows(transition_only)
    summary_path = os.path.join(output_dir, "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote {len(sequence_rows)} sequence records: {sequence_path}")
    print(f"Wrote {len(summary)} detector summaries: {summary_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results/attack_transition")
    parser.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    args = parser.parse_args()
    run(args.output_dir, tuple(args.seeds))
