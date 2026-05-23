# Canonical Model Correlation

These rows are filtered to one model, feature group, target, and optional split.
Selection: `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` + `delta_capacity_Ah` + split `c_rate_holdout_fold`.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_residual` | 143 | 0.375176 | 0.242712 |
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.647125 | 0.646779 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_residual` | 143 | 0.353684 | 0.257789 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 143 | 0.614595 | 0.633483 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 143 | 0.375176 | 0.242712 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.647125 | 0.646779 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 143 | 0.353684 | 0.257789 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 143 | 0.614595 | 0.633483 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_residual` | 44 | 0.268885 | 0.230444 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 44 | 0.532297 | 0.58661 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_residual` | 44 | 0.249866 | 0.242283 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 44 | 0.512939 | 0.596195 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 27 | -0.0287528 | 0.0543346 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 27 | 0.384575 | 0.385226 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 27 | -0.0465212 | 0.106838 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 27 | 0.384759 | 0.484127 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 33 | 0.753961 | 0.591912 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 33 | 0.862959 | 0.821524 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 33 | 0.737104 | 0.639372 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 33 | 0.83891 | 0.830548 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 0 | NA | NA |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 0 | NA | NA |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 0 | NA | NA |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 0 | NA | NA |
