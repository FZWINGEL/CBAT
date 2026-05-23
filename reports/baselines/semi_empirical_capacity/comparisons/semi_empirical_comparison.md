# Semi-Empirical Baseline Comparison

Positive gain means the semi-empirical ridge comparator has lower condition MAE than the reference.

| Reference | Target | Split | Semi group | Reference group | Conditions | Mean gain | Win rate |
|---|---|---|---|---|---:|---:|---:|
| `hgb_f4` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 12 | -0.0979716 | 0.166667 |
| `hgb_f4` | `capacity_Ah_k1` | `condition_fold` | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 76 | -0.0270801 | 0.105263 |
| `hgb_f4` | `capacity_Ah_k1` | `profile_holdout_fold` | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 12 | 0.00417803 | 0.666667 |
| `hgb_f4` | `capacity_Ah_k1` | `temperature_holdout_fold` | `SE1_calendar_cycling` | `F4_state_log_age_scalar` | 38 | -0.046725 | 0.157895 |
| `hgb_f4` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `SE4_coupled_stress` | `F4_state_log_age_scalar` | 76 | -0.024878 | 0.421053 |
| `hgb_f4` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 12 | -0.121962 | 0.0833333 |
| `hgb_f4` | `delta_capacity_Ah` | `condition_fold` | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 76 | -0.0363378 | 0.0394737 |
| `hgb_f4` | `delta_capacity_Ah` | `profile_holdout_fold` | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 12 | 0.0290456 | 0.75 |
| `hgb_f4` | `delta_capacity_Ah` | `temperature_holdout_fold` | `SE1_calendar_cycling` | `F4_state_log_age_scalar` | 38 | -0.0675391 | 0.105263 |
| `hgb_f4` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `SE4_coupled_stress` | `F4_state_log_age_scalar` | 76 | -0.0351903 | 0.368421 |
| `best_stress` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `SE3_c_rate_interactions` | `F5_log_age_histograms` | 12 | -0.102553 | 0.166667 |
| `best_stress` | `capacity_Ah_k1` | `condition_fold` | `SE3_c_rate_interactions` | `F6_coupled_stress` | 76 | -0.0281158 | 0.0789474 |
| `best_stress` | `capacity_Ah_k1` | `temperature_holdout_fold` | `SE1_calendar_cycling` | `F6_coupled_stress` | 38 | -0.0519028 | 0.131579 |
| `best_stress` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `SE4_coupled_stress` | `F10_c_rate_v1_1` | 76 | -0.0138983 | 0.460526 |
| `best_stress` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `SE3_c_rate_interactions` | `F8_timestamp_weighted_stress` | 12 | -0.120579 | 0.166667 |
| `best_stress` | `delta_capacity_Ah` | `condition_fold` | `SE3_c_rate_interactions` | `F8_timestamp_weighted_stress` | 76 | -0.0392156 | 0.0657895 |
| `best_stress` | `delta_capacity_Ah` | `temperature_holdout_fold` | `SE1_calendar_cycling` | `F6_coupled_stress` | 38 | -0.0680422 | 0.0526316 |
| `best_stress` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `SE4_coupled_stress` | `F10_c_rate_v1_1` | 76 | -0.0344558 | 0.434211 |
