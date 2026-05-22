# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T22:17:01.155977+00:00`
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
| `L2_hist_gradient_boosting` | `F5_log_age_histograms` | `delta_capacity_Ah` | `condition_fold` | 0.0419474 | 0.171533 |
| `L2_hist_gradient_boosting` | `F6_coupled_stress` | `delta_capacity_Ah` | `condition_fold` | 0.0422553 | 0.172347 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0446449 | 0.183122 |
| `L3_quantile_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `condition_fold` | 0.0476644 | 0.287581 |
| `L2_hist_gradient_boosting` | `F6_coupled_stress` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0480717 | 0.141452 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0485748 | 0.168685 |
| `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0486837 | 0.147627 |
| `L2_hist_gradient_boosting` | `F5_log_age_histograms` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0488614 | 0.172006 |
| `L3_quantile_hist_gradient_boosting` | `F6_coupled_stress` | `delta_capacity_Ah` | `condition_fold` | 0.0491037 | 0.267342 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
