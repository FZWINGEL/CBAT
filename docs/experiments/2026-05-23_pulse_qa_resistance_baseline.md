# 2026-05-23 PULSE QA and Resistance Baseline

## Scope

Milestone 0.7 opens a scoped PULSE evidence stream after the LOG_AGE-only
C-rate delta pass did not beat the F4 threshold. This is not a multimodal model
and not a PULSE scientific claim. The work is QA-first and baseline-first:

```text
PULSE QA -> PULSE target policy -> PULSE target table -> scalar resistance baseline
```

EIS modeling, EIS embeddings, knee prediction, sequence models, neural models,
policy ranking, CBAT, and capacity+PULSE multimodal claims remain blocked.

## Policy

Created:

```text
docs/PULSE_TARGET_POLICY.md
```

Canonical target context:

```text
RT / 50% SOC
```

First baseline target:

```text
delta_pulse_1s_resistance
```

Secondary targets are defined but not yet promoted as claims.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse qa \
  --pulse-summary data/interim/modality_table_pulse_summary.parquet \
  --checkup-table data/interim/checkup_event_table.parquet \
  --out reports/audit/pulse_qa_report.json \
  --coverage-out reports/audit/pulse_target_coverage.csv \
  --alignment-out reports/audit/pulse_alignment_report.json

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse build-targets \
  --pulse-summary data/interim/modality_table_pulse_summary.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/pulse_target_table.parquet \
  --soc-percent 50 \
  --temperature-context RT

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-pulse \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/pulse_resistance_l0_l3_report.json \
  --predictions-out data/processed/pulse_resistance_l0_l3_predictions.parquet \
  --model-levels L0_persistence,L1_ridge,L2_hist_gradient_boosting \
  --feature-groups P0_persistence,P1_state_time,P2_state_capacity,P3_state_nominal,P4_state_log_age_scalar,P5_stress_v1_1 \
  --targets delta_pulse_1s_resistance \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50
```

## QA Outputs

```text
reports/audit/pulse_qa_report.json
reports/audit/pulse_alignment_report.json
reports/audit/pulse_target_coverage.csv
data/interim/pulse_target_table.parquet
```

The target table is generated data and remains ignored.

## QA Findings

PULSE summary QA:

| Field | Value |
|---|---:|
| Rows | `39,365` |
| Unique cells | `228` |
| Canonical RT/50% cell-checkups available | `3,980` |
| Canonical RT/50% cell-checkups missing | `75` |
| Duplicate canonical cell-checkups | `0` |
| Large alignment-delta rows > 1 day | `5,060` |

Alignment delta summary:

| Statistic | Seconds |
|---|---:|
| min | `1,775` |
| median | `41,485` |
| p95 | `108,598` |
| max | `192,748` |

Canonical interval target table:

| Target field | Finite intervals |
|---|---:|
| `pulse_1s_resistance_k` | `3,826` |
| `pulse_1s_resistance_k1` | `3,752` |
| `delta_pulse_1s_resistance` | `3,751` |
| `delta_pulse_10ms_resistance` | `3,751` |

Quality flags:

| Flag | Count |
|---|---:|
| `OK` | `3,751` |
| `missing_pulse_k1` | `75` |
| `missing_pulse_k` | `1` |

Decision: the RT/50% canonical target is usable for a first baseline but must be
reported with missingness and large alignment-delta warnings. This does not yet
support a scientific PULSE claim.

## Baseline Outputs

```text
reports/baselines/pulse_resistance_l0_l3_report.json
reports/baselines/pulse_resistance_l0_l3/leaderboard.csv
reports/baselines/pulse_resistance_l0_l3/baseline_summary.md
reports/baselines/pulse_resistance_l0_l3/pulse_diagnostics.md
reports/baselines/pulse_resistance_l0_l3/plots/pulse_target_coverage_by_split.csv
```

Prediction Parquet remains ignored:

```text
data/processed/pulse_resistance_l0_l3_predictions.parquet
```

## First Baseline Findings

Best primary rows by split for `delta_pulse_1s_resistance`:

| Split | Best model | Feature group | Condition-mean MAE | Worst-condition MAE | Test rows |
|---|---|---|---:|---:|---:|
| `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | `0.000960407` | `0.00357084` | `3,751` |
| `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | `0.00109610` | `0.00437046` | `1,756` |
| `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | `0.00185842` | `0.00460596` | `143` |
| `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | `0.000953406` | `0.00278087` | `733` |
| `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | `0.00117733` | `0.00517459` | `3,751` |

Initial interpretation:

- PULSE RT/50% resistance is predictable enough to justify further QA and
  baseline hardening.
- C-rate holdout is again one of the harder views and has limited target rows
  (`143` in this first report), so it should not be overinterpreted.
- Stress features help condition and temperature folds, but nominal/state
  features are better on C-rate in this first pass.
- No PULSE scientific claim is authorized yet; this is a baseline diagnostic.

## Validation

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check src/mbp/data/products/pulse_targets.py src/mbp/baselines/pulse.py src/mbp/cli.py tests/test_pulse_targets.py tests/test_pulse_baselines.py src/mbp/data/luh_blank/qa_result_data.py
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest tests/test_pulse_targets.py tests/test_pulse_baselines.py -q
5 passed

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
96 passed
```
