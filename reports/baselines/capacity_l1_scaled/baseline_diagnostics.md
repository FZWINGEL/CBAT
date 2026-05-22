# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_l1_scaled_report.json`
Generated at UTC: `2026-05-22T15:10:45.816579+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `10`
Numeric standardization: `train_fold_mean_std`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---:|---:|
| `delta_capacity_Ah` | `profile_holdout_fold` | `L1_ridge` | `F0_time_only` | 0.0730731 | 0.0230865 | 67 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `L1_ridge` | `F2_state_exposure` | 0.0775796 | 0.0185801 | 67 |
| `delta_capacity_Ah` | `condition_fold` | `L1_ridge` | `F4_state_log_age_scalar` | 0.0782155 | 0.0597952 | 23 |
| `capacity_Ah_k1` | `condition_fold` | `L1_ridge` | `F4_state_log_age_scalar` | 0.0782245 | 0.0597862 | 23 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0869256 | 0.031801 | 23 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.086994 | 0.0317326 | 23 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0892905 | 0.0609659 | 23 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0893865 | 0.0608699 | 23 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.176993 | 0.157861 | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.177045 | 0.157809 | 36 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded full run.

| Target | Best model | Feature group | Condition mean MAE | Improvement vs L0 |
|---|---|---|---:|---:|
| `capacity_Ah_k1` | `L1_ridge` | `F3_state_nominal` | 0.176993 | 0.157861 |
| `delta_capacity_Ah` | `L1_ridge` | `F3_state_nominal` | 0.177045 | 0.157809 |

## Feature Gains

Primary feature-gain rows: `30`
Mean primary adjacent-feature gain: `-0.0250795`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `144`
Mean primary-minus-sensitivity condition-mean MAE: `0.00153689`
Median primary-minus-sensitivity condition-mean MAE: `0.00140974`

## Diagnostic Tables

- `plots/best_by_target_split.csv`
- `plots/feature_gain_by_split.csv`
- `plots/c_rate_holdout_errors.csv`
- `plots/c_rate_holdout_by_condition.csv`
- `plots/strict_vs_tolerant_delta.csv`
- `plots/worst_condition_errors.csv`
- `c_rate_holdout_error_analysis.md`

C-rate diagnostic rows: `24`
