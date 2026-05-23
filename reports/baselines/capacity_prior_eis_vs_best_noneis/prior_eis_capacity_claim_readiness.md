# Prior-EIS Capacity Claim Readiness

This report compares prior-EIS feature groups against the strongest supplied non-EIS groups on the same EIS-covered prediction population.
It does not authorize broad EIS, DRT, embedding, neural, CBAT, or multimodal claims.

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| Prior EIS beats strongest non-EIS for capacity primary target | `supported` | 1 split rows have bootstrap p05 > 0; C-rate mean -0.0052792, p05 -0.0139444 | Allow only narrow split-specific EIS claim |
| Prior EIS improves delta_capacity_Ah | `not_supported` | C-rate mean 0.00339262, p05 -0.00894379 | Do not claim fade-rate improvement |
| Leakage safety | `supported` | Only prior EIS `k` scalar features are allowed for non-EIS targets. | Future EIS state, EIS deltas, R0/R1, DRT, and embeddings remain blocked. |

## Paired Gain Summary

| Target | Split | Prior-EIS group | Non-EIS group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `C_E2_log_age_eis` | `F5_log_age_histograms` | 12 | -0.0052792 | -0.0139444 | -0.00508302 | 0.00374281 | 0.416667 |
| `capacity_Ah_k1` | `condition_fold` | `C_E2_log_age_eis` | `F6_coupled_stress` | 76 | -0.000494574 | -0.00323048 | -0.000491376 | 0.00210026 | 0.486842 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `C_E0_state_time_eis` | `F1_state_time` | 12 | 0.00676548 | 0.00384062 | 0.00650819 | 0.00980382 | 0.833333 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `C_E3_stress_eis` | `F6_coupled_stress` | 38 | -0.000417496 | -0.00333562 | -0.000327461 | 0.00229762 | 0.394737 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `C_E2_log_age_eis` | `F4_state_log_age_scalar` | 76 | 5.10611e-05 | -0.00251256 | 0.000120212 | 0.00249478 | 0.565789 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `C_E3_stress_eis` | `F4_state_log_age_scalar` | 12 | 0.00339262 | -0.00894379 | 0.00344712 | 0.0145997 | 0.666667 |
| `delta_capacity_Ah` | `condition_fold` | `C_E3_stress_eis` | `F8_timestamp_weighted_stress` | 76 | -0.00152554 | -0.00268751 | -0.00151864 | -0.000451768 | 0.447368 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `C_E0_state_time_eis` | `F1_state_time` | 12 | 0.0076398 | 0.00428472 | 0.00742466 | 0.0109501 | 0.833333 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `C_E2_log_age_eis` | `F6_coupled_stress` | 38 | -0.00259837 | -0.00761449 | -0.0025343 | 0.00225541 | 0.447368 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `C_E2_log_age_eis` | `F4_state_log_age_scalar` | 76 | 0.000734093 | -0.00181625 | 0.000626923 | 0.003348 | 0.486842 |
