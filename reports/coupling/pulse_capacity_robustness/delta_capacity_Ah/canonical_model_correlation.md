# Canonical Model Correlation

These rows are filtered to one model, feature group, target, and optional split.
Selection: `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` + `delta_capacity_Ah` + split `all`.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_residual` | 10134 | 0.301629 | 0.0699996 |
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 10134 | 0.381418 | 0.277899 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_residual` | 10134 | 0.310183 | 0.0892346 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 10134 | 0.368487 | 0.239452 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 506 | 0.376234 | 0.248775 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 506 | 0.423024 | 0.372425 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 506 | 0.350132 | 0.247039 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 506 | 0.400684 | 0.380064 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_residual` | 300 | 0.46365 | 0.450442 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 300 | 0.258849 | 0.238417 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_residual` | 300 | 0.44455 | 0.4409 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 300 | 0.25253 | 0.253461 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 3470 | 0.362906 | 0.21883 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 3470 | 0.244228 | 0.110311 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 3470 | 0.372132 | 0.203579 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 3470 | 0.268705 | 0.13314 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 1206 | 0.612241 | 0.297785 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 1206 | 0.654124 | 0.376995 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 1206 | 0.59294 | 0.294002 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 1206 | 0.623678 | 0.356645 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 2558 | 0.400182 | 0.140242 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 2558 | 0.262943 | 0.0905329 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 2558 | 0.417844 | 0.139316 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 2558 | 0.267817 | 0.0976309 |
