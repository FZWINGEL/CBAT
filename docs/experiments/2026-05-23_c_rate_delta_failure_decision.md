# 2026-05-23 C-Rate Delta Failure Decision

## Scope

Milestone 0.6.3 is a capacity-only, scalar-feature-only check of the remaining
C-rate `delta_capacity_Ah` failure. It does not add EIS/PULSE features, knee
labels, sequence models, neural models, policy ranking, or CBAT.

The question was whether the C-rate delta failure could be fixed by one of three
narrow changes:

1. normalized delta-rate targets;
2. train-fold residual/bias correction;
3. compact cold/current LOG_AGE stress feature groups.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_delta_rate_targets_hgb50_report.json \
  --predictions-out data/processed/capacity_delta_rate_targets_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress,F11_minimal_cold_current,F12_voltage_cold_current_interactions,F13_sparse_c_rate_context \
  --targets delta_capacity_Ah,delta_capacity_per_day_target,delta_capacity_per_efc_target \
  --split-views c_rate_holdout_fold \
  --hgb-max-iter 50

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json \
  --predictions-out data/processed/capacity_c_rate_delta_v1_2_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress,F11_minimal_cold_current,F12_voltage_cold_current_interactions,F13_sparse_c_rate_context \
  --targets delta_capacity_Ah \
  --split-views c_rate_holdout_fold,condition_fold,temperature_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_c_rate_bias_corrected_report.json \
  --predictions-out data/processed/capacity_c_rate_bias_corrected_predictions.parquet \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress,F11_minimal_cold_current,F12_voltage_cold_current_interactions,F13_sparse_c_rate_context \
  --targets delta_capacity_Ah \
  --split-views c_rate_holdout_fold,condition_fold,temperature_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50 \
  --bias-correction

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline diagnose-stress-features \
  --report reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json \
  --baseline-report reports/baselines/capacity_hgb50_focused_report.json \
  --l0-reference-report reports/baselines/capacity_l0_l3_report.json \
  --out-dir reports/baselines/capacity_c_rate_delta_v1_2_hgb50
```

## Outputs

```text
reports/baselines/capacity_delta_rate_targets_hgb50_report.json
reports/baselines/capacity_delta_rate_targets_hgb50/plots/rate_target_vs_direct_delta.csv
reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json
reports/baselines/capacity_c_rate_delta_v1_2_hgb50/stress_feature_diagnostics.md
reports/baselines/capacity_c_rate_bias_corrected_report.json
reports/baselines/capacity_c_rate_bias_corrected/plots/bias_correction_by_split.csv
reports/baselines/capacity_c_rate_bias_corrected/plots/c_rate_bias_before_after.csv
```

Prediction Parquets under `data/processed/` are generated local artifacts and
remain ignored.

## Findings

### Normalized Rate Targets

Normalized target modes train on delta rate and evaluate predictions back in
`delta_capacity_Ah` units.

Best C-rate rows:

| Target mode | Feature group | C-rate condition-mean MAE |
|---|---|---:|
| `delta_capacity_Ah` | `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_per_day_target` | `F8_timestamp_weighted_stress` | `0.121271` |
| `delta_capacity_per_efc_target` | no better than direct delta in this run | worse than direct F4 |

Decision: normalized rate targets do not beat direct delta on C-rate and should
not become the primary target path.

### Narrow Cold/Current Feature Groups

The narrow direct-delta pass tested F11-F13 against F4 and F8.

| Feature group | C-rate `delta_capacity_Ah` condition-mean MAE |
|---|---:|
| `F4_state_log_age_scalar` | `0.101133` |
| `F8_timestamp_weighted_stress` | `0.102516` |
| `F13_sparse_c_rate_context` | `0.147452` |
| `F11_minimal_cold_current` | `0.149436` |
| `F12_voltage_cold_current_interactions` | `0.162640` |

F11-F13 do not beat F4 or F8 on the C-rate delta target. The compact feature
sets are too narrow or too sparse to solve the held-out C-rate delta failure.

Other folds did not reveal a hidden win for C-rate delta:

| Split | F4 baseline | Best tested group | Best condition-mean MAE | Gain vs F4 |
|---|---:|---|---:|---:|
| `condition_fold` | `0.044645` | `F8_timestamp_weighted_stress` | `0.041700` | `0.002945` |
| `temperature_holdout_fold` | `0.048575` | `F4_state_log_age_scalar` | `0.048575` | `0.000000` |
| `voltage_window_holdout_fold` | `0.070845` | `F13_sparse_c_rate_context` | `0.062451` | `0.008394` |
| `c_rate_holdout_fold` | `0.101133` | `F4_state_log_age_scalar` | `0.101133` | `0.000000` |

### Train-Fold Bias Correction

The residual correction layer was fit only on train rows, grouped by nominal
temperature, voltage-window family, and charge-rate bucket, then applied to test
predictions. It did not materially change the C-rate delta result. The best
C-rate changes were at numerical-noise scale, for example F4 changed from
`0.10113277130259181` to `0.10113277130214215`.

Decision: residual correction is neutral and should remain diagnostic only.

## Decision

The 0.6.3 success criterion was:

```text
C-rate delta_capacity_Ah condition-mean MAE < 0.101133
preferably >= 0.005 absolute or >= 5% relative improvement
no material degradation in condition, temperature, or voltage-window folds
```

No 0.6.3 approach met the threshold.

Therefore:

- Keep direct `delta_capacity_Ah` as the primary C-rate delta target.
- Do not promote normalized rate targets.
- Do not promote F11-F13 narrow cold/current groups.
- Keep train-fold residual correction as a diagnostic only.
- Stop broad LOG_AGE scalar stress-feature expansion unless a concrete bug is
  found.
- The next recommended direction is a scoped PULSE QA/baseline milestone as an
  independent evidence stream.

EIS/PULSE supervised claims, knee prediction, sequence models, neural models,
policy ranking, and CBAT remain blocked until explicitly authorized by the next
milestone.

## Validation

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check src/mbp/baselines/capacity.py src/mbp/cli.py tests/test_capacity_baselines.py
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest tests/test_capacity_baselines.py -q
24 passed

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
91 passed, 1 warning
```
