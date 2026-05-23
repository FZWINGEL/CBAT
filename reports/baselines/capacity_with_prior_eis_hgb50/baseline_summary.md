# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-23T13:30:45.177542+00:00`
Primary subset: `baseline_clean_tolerant`

## Row Counts

| Count | Value |
|---|---:|
| `full_interval_rows` | 3827 |
| `selected_subset_rows` | 3821 |
| `sensitivity_excluding_monotonicity_rows` | 2769 |
| `baseline_clean_strict_rows` | 2773 |
| `baseline_clean_tolerant_rows` | 3827 |
| `sensitivity_flagged_monotonicity_rows` | 1054 |
| `selected_cells` | 228 |
| `selected_parameter_sets` | 76 |

## Best Primary Rows

| Model | Feature group | Target | Split | Condition mean MAE | Worst condition MAE |
|---|---|---|---|---:|---:|
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `condition_fold` | 0.042764 | 0.173554 |
| `L2_hist_gradient_boosting` | `C_E3_stress_eis` | `delta_capacity_Ah` | `condition_fold` | 0.0432383 | 0.185825 |
| `L2_hist_gradient_boosting` | `C_E2_log_age_eis` | `delta_capacity_Ah` | `condition_fold` | 0.0442126 | 0.175977 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0448822 | 0.180876 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0500752 | 0.166103 |
| `L2_hist_gradient_boosting` | `C_E2_log_age_eis` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0508802 | 0.16475 |
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0518144 | 0.138676 |
| `L2_hist_gradient_boosting` | `C_E3_stress_eis` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0526924 | 0.14788 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `capacity_Ah_k1` | `condition_fold` | 0.0530431 | 0.244106 |
| `L2_hist_gradient_boosting` | `C_E2_log_age_eis` | `capacity_Ah_k1` | `condition_fold` | 0.0533774 | 0.254653 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
