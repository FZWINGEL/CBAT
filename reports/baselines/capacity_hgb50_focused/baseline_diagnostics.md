# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_hgb50_focused_report.json`
Generated at UTC: `2026-05-22T15:10:46.310418+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0446449 | NA | 20 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0485748 | NA | 67 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0539267 | NA | 23 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `F1_state_time` | 0.0621921 | NA | 70 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `L3_quantile_hist_gradient_boosting` | `F1_state_time` | 0.0650827 | NA | 67 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L3_quantile_hist_gradient_boosting` | `F1_state_time` | 0.068512 | NA | 32 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0692939 | NA | 23 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0844129 | NA | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | NA | 20 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.125186 | NA | 36 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded full run.

| Target | Best model | Feature group | Condition mean MAE | Improvement vs L0 |
|---|---|---|---:|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | NA |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.125186 | NA |

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
- `plots/strict_vs_tolerant_delta.csv`
- `plots/worst_condition_errors.csv`
- `c_rate_holdout_error_analysis.md`

C-rate diagnostic rows: `24`
