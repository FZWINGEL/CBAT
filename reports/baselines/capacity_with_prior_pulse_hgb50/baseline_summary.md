# Capacity Baseline Summary

Schema version: `gate5.capacity_baseline.v1`
Generated at UTC: `2026-05-23T09:20:17.131093+00:00`
Primary subset: `baseline_clean_tolerant`

## Row Counts

| Count | Value |
|---|---:|
| `full_interval_rows` | 3827 |
| `selected_subset_rows` | 3826 |
| `sensitivity_excluding_monotonicity_rows` | 2772 |
| `baseline_clean_strict_rows` | 2773 |
| `baseline_clean_tolerant_rows` | 3827 |
| `sensitivity_flagged_monotonicity_rows` | 1054 |
| `selected_cells` | 228 |
| `selected_parameter_sets` | 76 |

## Best Primary Rows

| Model | Feature group | Target | Split | Condition mean MAE | Worst condition MAE |
|---|---|---|---|---:|---:|
| `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | `delta_capacity_Ah` | `condition_fold` | 0.0427605 | 0.172266 |
| `L2_hist_gradient_boosting` | `C_P2_log_age_pulse` | `delta_capacity_Ah` | `condition_fold` | 0.0448505 | 0.181176 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `condition_fold` | 0.0452556 | 0.182239 |
| `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0487602 | 0.156282 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0497915 | 0.173625 |
| `L2_hist_gradient_boosting` | `C_P2_log_age_pulse` | `delta_capacity_Ah` | `temperature_holdout_fold` | 0.0502525 | 0.186973 |
| `L2_hist_gradient_boosting` | `C_P2_log_age_pulse` | `capacity_Ah_k1` | `condition_fold` | 0.0531232 | 0.242652 |
| `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | `capacity_Ah_k1` | `condition_fold` | 0.0533402 | 0.231441 |
| `L2_hist_gradient_boosting` | `C_P3_stress_pulse` | `capacity_Ah_k1` | `condition_fold` | 0.0549543 | 0.271346 |
| `L2_hist_gradient_boosting` | `C_P1_nominal_pulse` | `delta_capacity_Ah` | `condition_fold` | 0.0595578 | 0.255596 |

## Artifacts

- `leaderboard.csv`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`
