# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
Generated at UTC: `2026-05-22T22:52:10.174971+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`
L0 reference report: `reports/baselines/capacity_l0_l3_report.json`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.0417003 | `reference_report` | 0.0963104 | 70 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0485748 | `reference_report` | 0.101682 | 67 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F13_sparse_c_rate_context` | 0.062451 | `reference_report` | 0.0562757 | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 | 20 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 |

## Feature Gains

Primary feature-gain rows: `8`
Mean primary adjacent-feature gain: `0.00214535`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `55`
Mean primary-minus-sensitivity condition-mean MAE: `-0.00431706`
Median primary-minus-sensitivity condition-mean MAE: `-0.00142813`

## Diagnostic Tables

- `plots/best_by_target_split.csv`
- `plots/feature_gain_by_split.csv`
- `plots/c_rate_holdout_errors.csv`
- `plots/c_rate_holdout_by_condition.csv`
- `plots/c_rate_grouped_summaries.csv`
- `plots/strict_vs_tolerant_delta.csv`
- `plots/worst_condition_errors.csv`
- `c_rate_holdout_error_analysis.md`
- `claim_readiness.md`

C-rate diagnostic rows: `12`
C-rate grouped summary rows: `30`
