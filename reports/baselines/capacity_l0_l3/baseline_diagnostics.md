# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_l0_l3_report.json`
Generated at UTC: `2026-05-22T15:27:59.561438+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `5`
Numeric standardization: `none`
L0 reference report: `none`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `F1_state_time` | 0.0699395 | `current_report` | 0.0262202 | 67 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `L1_ridge` | `F2_state_exposure` | 0.0787354 | `current_report` | 0.0174242 | 67 |
| `delta_capacity_Ah` | `condition_fold` | `L1_ridge` | `F4_state_log_age_scalar` | 0.0812032 | `current_report` | 0.0568076 | 23 |
| `capacity_Ah_k1` | `condition_fold` | `L1_ridge` | `F4_state_log_age_scalar` | 0.0818194 | `current_report` | 0.0561913 | 23 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0865544 | `current_report` | 0.0321722 | 23 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0870353 | `current_report` | 0.0316914 | 23 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0896394 | `current_report` | 0.060617 | 23 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.0914024 | `current_report` | 0.0588539 | 23 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.175406 | `current_report` | 0.159448 | 36 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L1_ridge` | `F3_state_nominal` | 0.175561 | `current_report` | 0.159293 | 36 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L1_ridge` | `F3_state_nominal` | 0.175406 | `current_report` | 0.159448 |
| `capacity_Ah_k1` | `L1_ridge` | `F3_state_nominal` | 0.175561 | `current_report` | 0.159293 |

## Feature Gains

Primary feature-gain rows: `90`
Mean primary adjacent-feature gain: `-0.00847721`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `384`
Mean primary-minus-sensitivity condition-mean MAE: `-8.73375e-05`
Median primary-minus-sensitivity condition-mean MAE: `0.000346153`

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
