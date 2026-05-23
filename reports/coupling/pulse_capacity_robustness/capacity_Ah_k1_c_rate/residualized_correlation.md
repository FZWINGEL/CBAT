# Residualized Correlation

Residualization controls for observed state and condition metadata.
This is a diagnostic association check, not causal evidence.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `diagnostic` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.838145 | 0.627044 |
| `diagnostic` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.838145 | 0.627044 |
| `diagnostic` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 44 | 0.886347 | 0.813249 |
| `diagnostic` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 27 | 0.885557 | 0.727717 |
| `diagnostic` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 33 | 0.98418 | 0.962233 |
| `diagnostic` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 0 | NA | NA |
