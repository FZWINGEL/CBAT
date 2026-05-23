# Prior-PULSE Capacity Predictive Claim Readiness

This Milestone 0.9 report tests a narrow non-neural claim: prior PULSE
state at check-up `k` may improve `capacity_Ah_k1` prediction under
grouped validation. It does not authorize broad multimodal claims, future
PULSE leakage, EIS, sequence models, neural models, policy ranking, or CBAT.

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| Prior PULSE improves capacity_Ah_k1 under OOD splits | `supported` | C-rate gain mean 0.00669208, bootstrap p05 0.000718651; temperature p05 0.0010323 | Allow a narrow level-prediction claim |
| Prior PULSE improves delta_capacity_Ah | `not_supported` | C-rate delta gain mean -0.0057423, bootstrap p05 -0.0203466 | Do not claim fade-rate improvement |
| Coverage loss changes fold composition | `not_supported` | Dropped intervals: 1; parameter sets: 76 | Coverage loss is small but must be reported |
| Leakage safety | `supported` | Prior-PULSE groups include `pulse_1s_resistance_k` and forbid future PULSE targets. | Keep future PULSE state and deltas blocked. |

## Best Paired Gain Summary

| Target | Split | Prior-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `C_P3_stress_pulse` | 12 | 0.00669208 | 0.000718651 | 0.00678842 | 0.0131255 | 0.666667 |
| `capacity_Ah_k1` | `condition_fold` | `C_P2_log_age_pulse` | 76 | 0.000252864 | -0.000847874 | 0.000275611 | 0.00134236 | 0.539474 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `C_P0_state_time_pulse` | 12 | 0.0214905 | 0.0137834 | 0.0214668 | 0.0299696 | 0.916667 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `C_P3_stress_pulse` | 38 | 0.0050962 | 0.0010323 | 0.00493892 | 0.00974339 | 0.605263 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `C_P2_log_age_pulse` | 76 | 0.000314337 | -0.00152649 | 0.000310583 | 0.00201887 | 0.631579 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `C_P3_stress_pulse` | 12 | -0.0057423 | -0.0203466 | -0.00552136 | 0.00835579 | 0.5 |
| `delta_capacity_Ah` | `condition_fold` | `C_P3_stress_pulse` | 76 | 0.00244457 | -0.00118799 | 0.00256572 | 0.00605267 | 0.592105 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `C_P0_state_time_pulse` | 12 | 0.0433817 | 0.0314462 | 0.0431773 | 0.0547482 | 0.916667 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `C_P3_stress_pulse` | 38 | 0.0010313 | -0.00421893 | 0.00104477 | 0.00649051 | 0.5 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `C_P2_log_age_pulse` | 76 | 0.000873073 | -0.00122843 | 0.000901102 | 0.00325013 | 0.434211 |

## Coverage

| Scope | Target | Split | Capacity-only intervals | PULSE-covered intervals | Dropped | Parameter sets |
|---|---|---|---:|---:|---:|---:|
| `report_row_counts` | `all` | `all` | 3827 | 3826 | 1 | 76 |
| `prediction_interval_keys` | `capacity_Ah_k1` | `c_rate_holdout_fold` | 157 | 157 | 0 | 12 |
| `prediction_interval_keys` | `capacity_Ah_k1` | `condition_fold` | 3827 | 3826 | 1 | 76 |
| `prediction_interval_keys` | `capacity_Ah_k1` | `profile_holdout_fold` | 752 | 751 | 1 | 12 |
| `prediction_interval_keys` | `capacity_Ah_k1` | `temperature_holdout_fold` | 1802 | 1802 | 0 | 38 |
| `prediction_interval_keys` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | 3827 | 3826 | 1 | 76 |
| `prediction_interval_keys` | `delta_capacity_Ah` | `c_rate_holdout_fold` | 157 | 157 | 0 | 12 |
| `prediction_interval_keys` | `delta_capacity_Ah` | `condition_fold` | 3827 | 3826 | 1 | 76 |
| `prediction_interval_keys` | `delta_capacity_Ah` | `profile_holdout_fold` | 752 | 751 | 1 | 12 |
| `prediction_interval_keys` | `delta_capacity_Ah` | `temperature_holdout_fold` | 1802 | 1802 | 0 | 38 |
| `prediction_interval_keys` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | 3827 | 3826 | 1 | 76 |
