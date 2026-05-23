# Prior-PULSE Capacity Feature Gain

| Target | Split | Best PULSE feature group | Gain vs F4 condition-mean MAE | Status |
|---|---|---|---:|---|
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `C_P3_stress_pulse` | 0.00669208 | `supported` |
| `capacity_Ah_k1` | `condition_fold` | `C_P2_log_age_pulse` | 0.000217057 | `supported` |
| `capacity_Ah_k1` | `profile_holdout_fold` | `C_P0_state_time_pulse` | 0.0214905 | `supported` |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `C_P3_stress_pulse` | 0.0050962 | `supported` |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `C_P2_log_age_pulse` | 0.000771117 | `supported` |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `C_P3_stress_pulse` | -0.0057423 | `not_supported` |
| `delta_capacity_Ah` | `condition_fold` | `C_P3_stress_pulse` | 0.00249507 | `supported` |
| `delta_capacity_Ah` | `profile_holdout_fold` | `C_P0_state_time_pulse` | 0.0433817 | `supported` |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `C_P3_stress_pulse` | 0.0010313 | `supported` |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `C_P2_log_age_pulse` | 0.00313342 | `supported` |

Positive gain means the prior-PULSE feature group improved over `F4_state_log_age_scalar` on the same PULSE-covered interval population. This is a coupling diagnostic, not a multimodal architecture claim.
