# Residualized Correlation

Residualization controls for observed state and condition metadata.
This is a diagnostic association check, not causal evidence.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `diagnostic` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 3751 | 0.45122 | 0.251932 |
| `diagnostic` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.784667 | 0.491895 |
| `diagnostic` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 106 | 0.819945 | 0.70692 |
| `diagnostic` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 1092 | 0.248431 | 0.14173 |
| `diagnostic` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 502 | 0.793868 | 0.600285 |
| `diagnostic` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 733 | 0.286334 | 0.151782 |
