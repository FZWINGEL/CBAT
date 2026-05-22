# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_hgb50_focused_report.json`
Generated at UTC: `2026-05-22T15:28:00.570963+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`
L0 reference report: `reports/baselines/capacity_l0_l3_report.json`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0446449 | `reference_report` | 0.0933658 | 20 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0485748 | `reference_report` | 0.101682 | 67 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0539267 | `reference_report` | 0.0840841 | 23 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `F1_state_time` | 0.0621921 | `reference_report` | 0.0339675 | 70 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `L3_quantile_hist_gradient_boosting` | `F1_state_time` | 0.0650827 | `reference_report` | 0.031077 | 67 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L3_quantile_hist_gradient_boosting` | `F1_state_time` | 0.068512 | `reference_report` | 0.0502147 | 32 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0692939 | `reference_report` | 0.0809624 | 23 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0844129 | `reference_report` | 0.0343138 | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 | 20 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.125186 | `reference_report` | 0.209668 | 36 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.125186 | `reference_report` | 0.209668 |

## Feature Gains

Primary feature-gain rows: `60`
Mean primary adjacent-feature gain: `0.00195634`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `192`
Mean primary-minus-sensitivity condition-mean MAE: `-0.00243175`
Median primary-minus-sensitivity condition-mean MAE: `-0.00219424`

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

C-rate diagnostic rows: `24`
C-rate grouped summary rows: `31`
