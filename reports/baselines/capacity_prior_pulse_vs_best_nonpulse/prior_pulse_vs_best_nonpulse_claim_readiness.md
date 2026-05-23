# Prior-PULSE vs Strongest Non-PULSE Claim Readiness

This Milestone 0.9.1 report compares prior-PULSE feature groups against
the strongest supplied non-PULSE HGB feature group on the same
PULSE-covered interval population.

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| Prior PULSE beats strongest non-PULSE for capacity_Ah_k1 | `not_supported` | C-rate p05 -0.00553843; temperature p05 -0.00294184; profile p05 -0.00281975 | Claim only improvement over weaker baselines or selected splits |
| Prior PULSE beats strongest non-PULSE for delta_capacity_Ah | `not_supported` | C-rate delta mean -0.00234428; p05 -0.0169742 | Do not claim fade-rate improvement |
| Leakage safety | `supported` | Prior-PULSE groups allow `pulse_1s_resistance_k` only. | Future PULSE state and PULSE deltas remain blocked. |

## Paired Gain Summary

| Target | Split | Prior-PULSE group | Non-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `C_P3_stress_pulse` | `F5_log_age_histograms` | 12 | 0.000392605 | -0.00553843 | 0.000727887 | 0.0064552 | 0.5 |
| `capacity_Ah_k1` | `condition_fold` | `C_P2_log_age_pulse` | `F6_coupled_stress` | 76 | -0.00036247 | -0.00302473 | -0.000320961 | 0.00225552 | 0.473684 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `C_P0_state_time_pulse` | `F1_state_time` | 12 | -0.000697582 | -0.00281975 | -0.00058227 | 0.00111274 | 0.583333 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `C_P3_stress_pulse` | `F6_coupled_stress` | 38 | -0.000753049 | -0.00294184 | -0.000680351 | 0.0012369 | 0.552632 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `C_P2_log_age_pulse` | `F4_state_log_age_scalar` | 76 | -0.000873658 | -0.00256428 | -0.000842818 | 0.000866917 | 0.605263 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `C_P3_stress_pulse` | `F4_state_log_age_scalar` | 12 | -0.00234428 | -0.0169742 | -0.00185231 | 0.0119867 | 0.583333 |
| `delta_capacity_Ah` | `condition_fold` | `C_P3_stress_pulse` | `F8_timestamp_weighted_stress` | 76 | -0.00108027 | -0.00209241 | -0.00107542 | -8.84982e-05 | 0.381579 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `C_P0_state_time_pulse` | `F1_state_time` | 12 | 3.01627e-05 | -0.00296854 | 0.000144961 | 0.00245299 | 0.583333 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `C_P3_stress_pulse` | `F6_coupled_stress` | 38 | -0.000688461 | -0.00259173 | -0.0007012 | 0.00125314 | 0.552632 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `C_P2_log_age_pulse` | `F4_state_log_age_scalar` | 76 | -0.000149101 | -0.00151388 | -0.00013384 | 0.00126314 | 0.539474 |
