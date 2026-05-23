# Canonical Model Correlation

These rows are filtered to one model, feature group, target, and optional split.
Selection: `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` + `capacity_Ah_k1` + split `all`.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_residual` | 10134 | 0.415472 | 0.11451 |
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 10134 | 0.497737 | 0.270488 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_residual` | 10134 | 0.429881 | 0.123386 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 10134 | 0.483696 | 0.241729 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 506 | 0.723272 | 0.488213 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 506 | 0.673092 | 0.386098 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 506 | 0.708519 | 0.509279 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 506 | 0.643049 | 0.368937 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_residual` | 300 | 0.740318 | 0.668439 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 300 | 0.664611 | 0.496066 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_residual` | 300 | 0.724047 | 0.662676 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 300 | 0.642575 | 0.486679 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 3470 | 0.322179 | 0.099833 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 3470 | 0.353684 | 0.24345 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 3470 | 0.358003 | 0.119496 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 3470 | 0.356556 | 0.229446 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 1206 | 0.77922 | 0.37877 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 1206 | 0.797387 | 0.396327 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 1206 | 0.762248 | 0.370925 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 1206 | 0.781933 | 0.383661 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 2558 | 0.313332 | 0.121593 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 2558 | 0.31941 | 0.159207 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 2558 | 0.337951 | 0.118739 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 2558 | 0.314214 | 0.159992 |
