# C-Rate Residual Analysis

This diagnostic uses row-level predictions for the best primary C-rate
selection per target in the focused stress-feature report.

| Target | Parameter set | Feature group | Temperature C | Voltage family | Intervals | MAE | Bias | RMSE |
|---|---:|---|---:|---|---:|---:|---:|---:|
| `capacity_Ah_k1` | 36 | `F5_log_age_histograms` | 10 | `approx_10_100` | 6 | 0.243035 | 0.243035 | 0.30042 |
| `capacity_Ah_k1` | 32 | `F5_log_age_histograms` | 10 | `approx_0_100` | 6 | 0.219295 | 0.219295 | 0.231946 |
| `delta_capacity_Ah` | 20 | `F4_state_log_age_scalar` | 0 | `approx_0_100` | 6 | 0.193506 | 0.0554402 | 0.201408 |
| `capacity_Ah_k1` | 20 | `F5_log_age_histograms` | 0 | `approx_0_100` | 6 | 0.17968 | 0.17968 | 0.199062 |
| `capacity_Ah_k1` | 24 | `F5_log_age_histograms` | 0 | `approx_10_100` | 4 | 0.165733 | 0.165733 | 0.173764 |
| `capacity_Ah_k1` | 60 | `F5_log_age_histograms` | 40 | `approx_10_100` | 16 | 0.145042 | 0.0834833 | 0.258273 |
| `delta_capacity_Ah` | 36 | `F4_state_log_age_scalar` | 10 | `approx_10_100` | 6 | 0.140919 | 0.140919 | 0.168015 |
| `delta_capacity_Ah` | 24 | `F4_state_log_age_scalar` | 0 | `approx_10_100` | 4 | 0.140443 | 0.101501 | 0.14569 |
| `delta_capacity_Ah` | 32 | `F4_state_log_age_scalar` | 10 | `approx_0_100` | 6 | 0.136856 | 0.136856 | 0.139735 |
| `delta_capacity_Ah` | 60 | `F4_state_log_age_scalar` | 40 | `approx_10_100` | 16 | 0.128406 | 0.0324072 | 0.217882 |
| `capacity_Ah_k1` | 44 | `F5_log_age_histograms` | 25 | `approx_0_100` | 6 | 0.110714 | 0.110714 | 0.163618 |
| `capacity_Ah_k1` | 28 | `F5_log_age_histograms` | 0 | `approx_10_90` | 9 | 0.102457 | 0.0631705 | 0.148332 |

## Outputs

- `plots/c_rate_residuals_by_parameter_set.csv`
- `plots/c_rate_residuals_by_temperature.csv`
- `plots/c_rate_residuals_by_voltage_window.csv`
- `plots/c_rate_residuals_by_capacity_bin.csv`
- `plots/c_rate_residuals_by_interval_count.csv`
- `plots/c_rate_signed_error_summary.csv`
