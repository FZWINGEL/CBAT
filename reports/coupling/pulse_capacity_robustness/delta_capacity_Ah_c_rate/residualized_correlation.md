# Residualized Correlation

Residualization controls for observed state and condition metadata.
This is a diagnostic association check, not causal evidence.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `diagnostic` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.519771 | 0.44761 |
| `diagnostic` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.519771 | 0.44761 |
| `diagnostic` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 44 | 0.470647 | 0.351374 |
| `diagnostic` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 27 | 0.447197 | 0.432234 |
| `diagnostic` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 33 | 0.883491 | 0.85762 |
| `diagnostic` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 0 | NA | NA |
