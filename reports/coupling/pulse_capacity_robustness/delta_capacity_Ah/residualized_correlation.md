# Residualized Correlation

Residualization controls for observed state and condition metadata.
This is a diagnostic association check, not causal evidence.

| Level | Scope | Pulse | Residual | n | Pearson | Spearman |
|---|---|---|---|---:|---:|---:|
| `diagnostic` | `all` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 3751 | 0.330324 | 0.182004 |
| `diagnostic` | `c_rate_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 143 | 0.457775 | 0.325844 |
| `diagnostic` | `cold_c_rate` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 106 | 0.421003 | 0.349906 |
| `diagnostic` | `voltage_window_approx_0_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 1092 | 0.253019 | 0.152635 |
| `diagnostic` | `voltage_window_approx_10_100` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 502 | 0.631924 | 0.489249 |
| `diagnostic` | `profile_holdout` | `delta_pulse_1s_resistance` | `capacity_abs_residual` | 733 | 0.25791 | 0.0356712 |
