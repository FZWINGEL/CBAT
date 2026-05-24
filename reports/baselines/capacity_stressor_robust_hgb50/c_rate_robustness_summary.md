# Stressor-Robust Capacity C-Rate Summary

This report evaluates non-neural robust HGB variants under grouped validation. It does not authorize architecture, policy, or causal claims.

| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `capacity_Ah_k1` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.118158` | `0.256868` |
| `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `0.121781` | `0.353878` |
| `capacity_Ah_k1` | `R0_reference_hgb50` | `F8_timestamp_weighted_stress` | `0.122442` | `0.253991` |
| `capacity_Ah_k1` | `R4_worst_fold_selected_hgb` | `F8_timestamp_weighted_stress` | `0.122442` | `0.253991` |
| `capacity_Ah_k1` | `R0_reference_hgb50` | `F4_state_log_age_scalar` | `0.125186` | `0.276435` |
| `capacity_Ah_k1` | `R1_condition_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.125902` | `0.28405` |
| `capacity_Ah_k1` | `R2_stressor_balanced_hgb` | `F4_state_log_age_scalar` | `0.131708` | `0.285298` |
| `capacity_Ah_k1` | `R4_worst_fold_selected_hgb` | `F4_state_log_age_scalar` | `0.131708` | `0.285298` |
| `capacity_Ah_k1` | `R1_condition_balanced_hgb` | `F4_state_log_age_scalar` | `0.133495` | `0.312451` |
| `capacity_Ah_k1` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `0.143421` | `0.333632` |
| `delta_capacity_Ah` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.0705429` | `0.133845` |
| `delta_capacity_Ah` | `R1_condition_balanced_hgb` | `F4_state_log_age_scalar` | `0.0813137` | `0.179341` |
| `delta_capacity_Ah` | `R2_stressor_balanced_hgb` | `F4_state_log_age_scalar` | `0.0824945` | `0.153564` |
| `delta_capacity_Ah` | `R1_condition_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.087602` | `0.2031` |
| `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F4_state_log_age_scalar` | `0.0967614` | `0.199648` |
| `delta_capacity_Ah` | `R0_reference_hgb50` | `F4_state_log_age_scalar` | `0.101133` | `0.193506` |
| `delta_capacity_Ah` | `R4_worst_fold_selected_hgb` | `F4_state_log_age_scalar` | `0.101133` | `0.193506` |
| `delta_capacity_Ah` | `R0_reference_hgb50` | `F8_timestamp_weighted_stress` | `0.102516` | `0.211938` |
| `delta_capacity_Ah` | `R4_worst_fold_selected_hgb` | `F8_timestamp_weighted_stress` | `0.102516` | `0.211938` |
| `delta_capacity_Ah` | `R3_condition_bagged_hgb` | `F8_timestamp_weighted_stress` | `0.104173` | `0.208089` |

Best C-rate delta candidate: `R2_stressor_balanced_hgb` / `F8_timestamp_weighted_stress`.
Gain vs F4 reference: `0.0305899`.
Gain vs stress reference: `0.0319729`.
Paired condition gain p05 vs F4: `0.0216868`.
Paired condition gain p05 vs stress reference: `0.0165793`.

Paired condition gain rows: `13696`.
