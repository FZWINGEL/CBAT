# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_delta_rate_targets_hgb50_report.json`
Generated at UTC: `2026-05-22T22:50:34.995859+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`
L0 reference report: `none`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_missing` | reference_missing | 20 |
| `delta_capacity_per_day_target` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.121271 | `reference_missing` | reference_missing | 32 |
| `delta_capacity_per_efc_target` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F12_voltage_cold_current_interactions` | 0.238739 | `reference_missing` | reference_missing | 24 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_missing` | reference_missing |
| `delta_capacity_per_day_target` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.121271 | `reference_missing` | reference_missing |
| `delta_capacity_per_efc_target` | `L2_hist_gradient_boosting` | `F12_voltage_cold_current_interactions` | 0.238739 | `reference_missing` | reference_missing |

## Feature Gains

Primary feature-gain rows: `6`
Mean primary adjacent-feature gain: `-0.0552779`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `15`
Mean primary-minus-sensitivity condition-mean MAE: `0.0107612`
Median primary-minus-sensitivity condition-mean MAE: `-0.00269755`

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

C-rate diagnostic rows: `36`
C-rate grouped summary rows: `32`
