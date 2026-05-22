# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T15:09:33.614090+00:00`
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
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0446449 | 0.183122 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0485748 | 0.168685 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `capacity_Ah_k1` | `condition_fold` | 0.0539267 | 0.258887 |
| `L3_quantile_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0557753 | 0.317662 |
| `L2_hist_gradient_boosting` | `F3_state_nominal` | `delta_capacity_Ah` | `condition_fold` | 0.0578797 | 0.230588 |
| `L2_hist_gradient_boosting` | `F3_state_nominal` | `capacity_Ah_k1` | `condition_fold` | 0.0588841 | 0.299999 |
| `L3_quantile_hist_gradient_boosting` | `F3_state_nominal` | `delta_capacity_Ah` | `condition_fold` | 0.0609227 | 0.314009 |
| `L2_hist_gradient_boosting` | `F2_state_exposure` | `delta_capacity_Ah` | `condition_fold` | 0.0610907 | 0.314076 |
| `L2_hist_gradient_boosting` | `F1_state_time` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.0621921 | 0.135459 |
| `L3_quantile_hist_gradient_boosting` | `F1_state_time` | `delta_capacity_Ah` | `condition_fold` | 0.0647256 | 0.371525 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
