# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T22:50:34.922131+00:00`
Primary subset: `baseline_clean_tolerant`

## Row Counts

| Count | Value |
|---|---:|
| `full_interval_rows` | 3827 |
| `selected_subset_rows` | 3827 |
| `sensitivity_excluding_monotonicity_rows` | 2773 |
| `baseline_clean_strict_rows` | 2773 |
| `baseline_clean_tolerant_rows` | 3827 |
| `sensitivity_flagged_monotonicity_rows` | 1054 |
| `selected_cells` | 228 |
| `selected_parameter_sets` | 76 |

## Best Primary Rows

| Model | Feature group | Target | Split | Condition mean MAE | Worst condition MAE |
|---|---|---|---|---:|---:|
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 0.101133 | 0.193506 |
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 0.102516 | 0.211938 |
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_per_day_target` | `c_rate_holdout_fold` | 0.121271 | 0.236558 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_per_day_target` | `c_rate_holdout_fold` | 0.132384 | 0.337998 |
| `L2_hist_gradient_boosting` | `F13_sparse_c_rate_context` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 0.147452 | 0.257372 |
| `L2_hist_gradient_boosting` | `F11_minimal_cold_current` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 0.149436 | 0.236575 |
| `L2_hist_gradient_boosting` | `F13_sparse_c_rate_context` | `delta_capacity_per_day_target` | `c_rate_holdout_fold` | 0.155854 | 0.287638 |
| `L2_hist_gradient_boosting` | `F12_voltage_cold_current_interactions` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 0.16264 | 0.275515 |
| `L2_hist_gradient_boosting` | `F11_minimal_cold_current` | `delta_capacity_per_day_target` | `c_rate_holdout_fold` | 0.164574 | 0.292642 |
| `L2_hist_gradient_boosting` | `F12_voltage_cold_current_interactions` | `delta_capacity_per_day_target` | `c_rate_holdout_fold` | 0.164754 | 0.310563 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
