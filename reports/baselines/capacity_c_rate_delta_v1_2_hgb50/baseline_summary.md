# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T22:51:03.406318+00:00`
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
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `condition_fold` | 0.0417003 | 0.190193 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0446449 | 0.183122 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0485748 | 0.168685 |
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0486837 | 0.147627 |
| `L2_hist_gradient_boosting` | `F12_voltage_cold_current_interactions` | `delta_capacity_Ah` | `condition_fold` | 0.0575802 | 0.305661 |
| `L2_hist_gradient_boosting` | `F11_minimal_cold_current` | `delta_capacity_Ah` | `condition_fold` | 0.0590228 | 0.273426 |
| `L2_hist_gradient_boosting` | `F13_sparse_c_rate_context` | `delta_capacity_Ah` | `condition_fold` | 0.0610916 | 0.284864 |
| `L2_hist_gradient_boosting` | `F13_sparse_c_rate_context` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0613705 | 0.293543 |
| `L2_hist_gradient_boosting` | `F13_sparse_c_rate_context` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | 0.062451 | 0.324434 |
| `L2_hist_gradient_boosting` | `F12_voltage_cold_current_interactions` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0648357 | 0.313436 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
