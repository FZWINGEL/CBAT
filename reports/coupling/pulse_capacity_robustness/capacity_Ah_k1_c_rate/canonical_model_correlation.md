# Canonical Model Correlation

These rows are filtered to one model, feature group, target, and optional split.
Selection: `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` + `capacity_Ah_k1` + split `c_rate_holdout_fold`.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_residual` | 143 | 0.81112 | 0.520035 |
| `canonical_prediction_row` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.857653 | 0.633959 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_residual` | 143 | 0.802652 | 0.546029 |
| `canonical_prediction_row` | `all` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 143 | 0.834578 | 0.611531 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 143 | 0.81112 | 0.520035 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.857653 | 0.633959 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 143 | 0.802652 | 0.546029 |
| `canonical_prediction_row` | `c_rate_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 143 | 0.834578 | 0.611531 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_residual` | 44 | 0.821249 | 0.700775 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 44 | 0.852047 | 0.740099 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_residual` | 44 | 0.810279 | 0.712333 |
| `canonical_prediction_row` | `cold_c_rate` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 44 | 0.837333 | 0.741508 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 27 | 0.7872 | 0.694139 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 27 | 0.842512 | 0.758852 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 27 | 0.795631 | 0.7558 |
| `canonical_prediction_row` | `voltage_window_approx_0_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 27 | 0.835574 | 0.810745 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_residual` | 33 | 0.956119 | 0.711898 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 33 | 0.971521 | 0.843583 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_residual` | 33 | 0.944306 | 0.733957 |
| `canonical_prediction_row` | `voltage_window_approx_10_100` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 33 | 0.956889 | 0.82988 |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_residual` | 0 | NA | NA |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 0 | NA | NA |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_residual` | 0 | NA | NA |
| `canonical_prediction_row` | `profile_holdout` | `delta_pulse_10ms_resistance` | `capacity_abs_residual` | 0 | NA | NA |
