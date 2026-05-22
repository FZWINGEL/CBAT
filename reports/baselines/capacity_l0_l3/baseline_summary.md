# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T14:50:09.651889+00:00`
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
| `L2_hist_gradient_boosting` | `F1_state_time` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0699395 | 0.231796 |
| `L3_quantile_hist_gradient_boosting` | `F1_state_time` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0720221 | 0.31022 |
| `L3_quantile_hist_gradient_boosting` | `F2_state_exposure` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0729453 | 0.307963 |
| `L1_ridge` | `F0_time_only` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0730727 | 0.26142 |
| `L3_quantile_hist_gradient_boosting` | `F3_state_nominal` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0737117 | 0.31194 |
| `L3_quantile_hist_gradient_boosting` | `F0_time_only` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.07439 | 0.305578 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0751212 | 0.243626 |
| `L3_quantile_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0780586 | 0.32116 |
| `L1_ridge` | `F2_state_exposure` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0780747 | 0.213959 |
| `L1_ridge` | `F2_state_exposure` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.0787354 | 0.213675 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
