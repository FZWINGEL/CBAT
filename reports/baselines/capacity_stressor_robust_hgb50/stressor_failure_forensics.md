# Stressor-Robust Failure Forensics

This report diagnoses where the existing robust-capacity near miss fails. It does not change the 5% non-degradation guardrail.

Current robust-capacity claim: `not_supported`.
Best candidate: `R2_stressor_balanced_hgb` / `F8_timestamp_weighted_stress`.
Max outside-C-rate relative degradation: `0.0528343`.

## Largest Split-Level Regressions

| Split | Target | Model | Feature | Relative degradation | MAE delta |
|---|---|---|---|---:|---:|
| `profile_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `0.333324` | `0.0275635` |
| `profile_holdout_fold` | `delta_capacity_Ah` | `R1_condition_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.319443` | `0.0264157` |
| `profile_holdout_fold` | `delta_capacity_Ah` | `R4_worst_fold_selected_hgb` | `F8_timestamp_weighted_stress` | `0.319443` | `0.0264157` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `0.210293` | `0.0266172` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R1_condition_balanced_hgb` | `F4_state_log_age_scalar` | `0.188328` | `0.013342` |
| `condition_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `0.11305` | `0.00471423` |
| `temperature_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `0.110919` | `0.00538784` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `0.0986987` | `0.00699228` |
| `profile_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `0.0968451` | `0.0105714` |
| `condition_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `0.0914981` | `0.00408492` |

## Largest Condition-Level Regressions

| Split | Target | Model | Feature | Parameter set | MAE delta | Relative degradation |
|---|---|---|---|---:|---:|---:|
| `condition_fold` | `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `1` | `0.156646` | `23.5774` |
| `temperature_holdout_fold` | `capacity_Ah_k1` | `R1_condition_balanced_hgb` | `F8_timestamp_weighted_stress` | `24` | `0.149211` | `3.47737` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `16` | `0.143354` | `0.863469` |
| `voltage_window_holdout_fold` | `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `24` | `0.130777` | `2.95466` |
| `condition_fold` | `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `9` | `0.122772` | `20.0831` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `8` | `0.115573` | `0.56733` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `4` | `0.115351` | `0.5655` |
| `voltage_window_holdout_fold` | `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `12` | `0.113465` | `0.55285` |
| `temperature_holdout_fold` | `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `24` | `0.108667` | `2.53249` |
| `condition_fold` | `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `13` | `0.104466` | `18.1936` |

Decision: use this for forensics only. Do not relax the 5% gate based on this report.
