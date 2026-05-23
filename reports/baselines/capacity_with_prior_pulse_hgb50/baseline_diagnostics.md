# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_with_prior_pulse_hgb50_report.json`
Generated at UTC: `2026-05-23T09:20:18.246414+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`
L0 reference report: `none`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | 0.0427605 | `reference_missing` | reference_missing | 67 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | 0.0487602 | `reference_missing` | reference_missing | 67 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `C_P2_log_age_pulse` | 0.0531232 | `reference_missing` | reference_missing | 23 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `C_P0_state_time_pulse` | 0.0618435 | `reference_missing` | reference_missing | 70 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | 0.0648692 | `reference_missing` | reference_missing | 23 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `C_P0_state_time_pulse` | 0.0654735 | `reference_missing` | reference_missing | 67 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `C_P2_log_age_pulse` | 0.0708683 | `reference_missing` | reference_missing | 36 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `C_P2_log_age_pulse` | 0.0839964 | `reference_missing` | reference_missing | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0977347 | `reference_missing` | reference_missing | 20 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | 0.120213 | `reference_missing` | reference_missing | 36 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0977347 | `reference_missing` | reference_missing |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | 0.120213 | `reference_missing` | reference_missing |

## Feature Gains

Primary feature-gain rows: `30`
Mean primary adjacent-feature gain: `0.000809427`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `120`
Mean primary-minus-sensitivity condition-mean MAE: `-0.00337561`
Median primary-minus-sensitivity condition-mean MAE: `-0.00345852`

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
