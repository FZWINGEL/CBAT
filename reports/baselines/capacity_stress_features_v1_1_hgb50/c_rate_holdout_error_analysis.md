# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F5_log_age_histograms` | 0.243035 | 0.557172 | 0.314137 |
| `capacity_Ah_k1` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F5_log_age_histograms` | 0.219295 | 0.556422 | 0.337127 |
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.193506 | 0.484002 | 0.290497 |
| `capacity_Ah_k1` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F5_log_age_histograms` | 0.17968 | 0.484002 | 0.304322 |
| `capacity_Ah_k1` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F5_log_age_histograms` | 0.165733 | 0.402438 | 0.236706 |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F5_log_age_histograms` | 0.145042 | 0.266788 | 0.121746 |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140919 | 0.557172 | 0.416253 |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140443 | 0.402438 | 0.261996 |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.136856 | 0.556422 | 0.419566 |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.128406 | 0.266788 | 0.138382 |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.138989 | 0.396189 | 0.257199 | 0.193506 |
| `10` | 6 | 3 | 54 | 0.144608 | 0.474212 | 0.329604 | 0.243035 |
| `25` | 6 | 3 | 88 | 0.0706071 | 0.243851 | 0.173244 | 0.110714 |
| `40` | 6 | 3 | 134 | 0.0892719 | 0.225164 | 0.135893 | 0.145042 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.139048 | 0.43965 | 0.300602 | 0.219295 |
| `approx_10_100` | 8 | 4 | 72 | 0.133336 | 0.347829 | 0.214493 | 0.243035 |
| `approx_10_90` | 8 | 4 | 180 | 0.0602232 | 0.217083 | 0.15686 | 0.102457 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.120605 | 0.334854 | 0.214249 | 0.243035 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.101133 | 0.334854 | 0.233721 | 0.193506 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.186593 | 0.484002 | 0.297409 | 0.193506 |
| `24` | 2 | 1 | 8 | 0.153088 | 0.402438 | 0.249351 | 0.165733 |
| `28` | 2 | 1 | 18 | 0.0772872 | 0.302125 | 0.224838 | 0.102457 |
| `32` | 2 | 1 | 12 | 0.178075 | 0.556422 | 0.378346 | 0.219295 |
| `36` | 2 | 1 | 12 | 0.191977 | 0.557172 | 0.365195 | 0.243035 |
| `40` | 2 | 1 | 30 | 0.063771 | 0.309043 | 0.245272 | 0.0732639 |
| `44` | 2 | 1 | 12 | 0.10362 | 0.414928 | 0.311308 | 0.110714 |
| `48` | 2 | 1 | 20 | 0.051555 | 0.164916 | 0.113361 | 0.0589442 |
| `52` | 2 | 1 | 56 | 0.0566462 | 0.151708 | 0.0950622 | 0.0590889 |
| `56` | 2 | 1 | 26 | 0.0879032 | 0.303248 | 0.215345 | 0.0927399 |
| `60` | 2 | 1 | 32 | 0.136724 | 0.266788 | 0.130064 | 0.145042 |
| `64` | 2 | 1 | 76 | 0.0431885 | 0.105457 | 0.0622685 | 0.0504568 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.0961327 | 0.293026 | 0.196894 | 0.145042 |
| `6-10` | 12 | 6 | 86 | 0.131518 | 0.413261 | 0.281743 | 0.243035 |
| `<=5` | 2 | 1 | 8 | 0.153088 | 0.402438 | 0.249351 | 0.165733 |
| `>20` | 4 | 2 | 132 | 0.0499174 | 0.128583 | 0.0786653 | 0.0590889 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.0772872 | 0.302125 | 0.224838 | 0.102457 |
| `2.6-2.8` | 10 | 5 | 78 | 0.131443 | 0.382205 | 0.250762 | 0.219295 |
| `<2.4` | 8 | 4 | 194 | 0.0750824 | 0.208249 | 0.133167 | 0.145042 |
| `>=2.8` | 4 | 2 | 24 | 0.147799 | 0.48605 | 0.338251 | 0.243035 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.0584896 | 0.20665 | 0.14816 | 0.102457 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.148283 | 0.426428 | 0.278145 | 0.243035 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
