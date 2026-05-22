# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-22T14:07:29.688980+00:00`
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
| `L0_persistence` | `persistence` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.0961596 | 0.351361 |
| `L0_persistence` | `persistence` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0961596 | 0.351361 |
| `L0_persistence` | `persistence` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | 0.118727 | 0.557172 |
| `L0_persistence` | `persistence` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | 0.118727 | 0.557172 |
| `L0_persistence` | `persistence` | `capacity_Ah_k1` | `condition_fold` | 0.138011 | 0.557172 |
| `L0_persistence` | `persistence` | `delta_capacity_Ah` | `condition_fold` | 0.138011 | 0.557172 |
| `L0_persistence` | `persistence` | `capacity_Ah_k1` | `temperature_holdout_fold` | 0.150256 | 0.496916 |
| `L0_persistence` | `persistence` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.150256 | 0.496916 |
| `L0_persistence` | `persistence` | `capacity_Ah_k1` | `c_rate_holdout_fold` | 0.334854 | 0.557172 |
| `L0_persistence` | `persistence` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 0.334854 | 0.557172 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
