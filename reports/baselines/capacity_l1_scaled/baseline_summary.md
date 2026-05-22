# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T15:08:17.424669+00:00`
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
| `L1_ridge` | `F0_time_only` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0730731 | 0.261425 |
| `L1_ridge` | `F2_state_exposure` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0775314 | 0.21452 |
| `L1_ridge` | `F2_state_exposure` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.0775796 | 0.214486 |
| `L1_ridge` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0782155 | 0.29888 |
| `L1_ridge` | `F4_state_log_age_scalar` | `capacity_Ah_k1` | `condition_fold` | 0.0782245 | 0.298793 |
| `L1_ridge` | `F1_state_time` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.0807132 | 0.209359 |
| `L1_ridge` | `F1_state_time` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0807395 | 0.209267 |
| `L1_ridge` | `F3_state_nominal` | `capacity_Ah_k1` | `condition_fold` | 0.0831872 | 0.342074 |
| `L1_ridge` | `F3_state_nominal` | `delta_capacity_Ah` | `condition_fold` | 0.0831944 | 0.341766 |
| `L1_ridge` | `F3_state_nominal` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0868214 | 0.301581 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
