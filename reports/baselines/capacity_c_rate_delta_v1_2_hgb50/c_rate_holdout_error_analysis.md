# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `12`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.193506 | 0.484002 | 0.290497 |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140919 | 0.557172 | 0.416253 |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140443 | 0.402438 | 0.261996 |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.136856 | 0.556422 | 0.419566 |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.128406 | 0.266788 | 0.138382 |
| `delta_capacity_Ah` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0965265 | 0.414928 | 0.318402 |
| `delta_capacity_Ah` | 56 | 40 | `approx_0_100` | 1.67 | 13 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0830665 | 0.303248 | 0.220182 |
| `delta_capacity_Ah` | 40 | 10 | `approx_10_90` | 1.67 | 15 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0732639 | 0.309043 | 0.235779 |
| `delta_capacity_Ah` | 52 | 25 | `approx_10_90` | 1.67 | 28 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0590889 | 0.151708 | 0.0926195 |
| `delta_capacity_Ah` | 48 | 25 | `approx_10_100` | 1.67 | 10 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0589442 | 0.164916 | 0.105972 |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 3 | 3 | 19 | 0.128689 | 0.396189 | 0.2675 | 0.193506 |
| `10` | 3 | 3 | 27 | 0.117013 | 0.474212 | 0.357199 | 0.140919 |
| `25` | 3 | 3 | 44 | 0.0715198 | 0.243851 | 0.172331 | 0.0965265 |
| `40` | 3 | 3 | 67 | 0.0873096 | 0.225164 | 0.137855 | 0.128406 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 4 | 4 | 31 | 0.127489 | 0.43965 | 0.312162 | 0.193506 |
| `approx_10_100` | 4 | 4 | 36 | 0.117178 | 0.347829 | 0.230651 | 0.140919 |
| `approx_10_90` | 4 | 4 | 90 | 0.0587317 | 0.217083 | 0.158352 | 0.0732639 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.101133 | 0.334854 | 0.233721 | 0.193506 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 1 | 1 | 6 | 0.193506 | 0.484002 | 0.290497 | 0.193506 |
| `24` | 1 | 1 | 4 | 0.140443 | 0.402438 | 0.261996 | 0.140443 |
| `28` | 1 | 1 | 9 | 0.0521174 | 0.302125 | 0.250008 | 0.0521174 |
| `32` | 1 | 1 | 6 | 0.136856 | 0.556422 | 0.419566 | 0.136856 |
| `36` | 1 | 1 | 6 | 0.140919 | 0.557172 | 0.416253 | 0.140919 |
| `40` | 1 | 1 | 15 | 0.0732639 | 0.309043 | 0.235779 | 0.0732639 |
| `44` | 1 | 1 | 6 | 0.0965265 | 0.414928 | 0.318402 | 0.0965265 |
| `48` | 1 | 1 | 10 | 0.0589442 | 0.164916 | 0.105972 | 0.0589442 |
| `52` | 1 | 1 | 28 | 0.0590889 | 0.151708 | 0.0926195 | 0.0590889 |
| `56` | 1 | 1 | 13 | 0.0830665 | 0.303248 | 0.220182 | 0.0830665 |
| `60` | 1 | 1 | 16 | 0.128406 | 0.266788 | 0.138382 | 0.128406 |
| `64` | 1 | 1 | 38 | 0.0504568 | 0.105457 | 0.0550002 | 0.0504568 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 3 | 3 | 44 | 0.094912 | 0.293026 | 0.198114 | 0.128406 |
| `6-10` | 6 | 6 | 43 | 0.113145 | 0.413261 | 0.300116 | 0.193506 |
| `<=5` | 1 | 1 | 4 | 0.140443 | 0.402438 | 0.261996 | 0.140443 |
| `>20` | 2 | 2 | 66 | 0.0547728 | 0.128583 | 0.0738099 | 0.0590889 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 1 | 1 | 9 | 0.0521174 | 0.302125 | 0.250008 | 0.0521174 |
| `2.6-2.8` | 5 | 5 | 39 | 0.122563 | 0.382205 | 0.259642 | 0.193506 |
| `<2.4` | 4 | 4 | 97 | 0.0778038 | 0.208249 | 0.130445 | 0.128406 |
| `>=2.8` | 2 | 2 | 12 | 0.118723 | 0.48605 | 0.367327 | 0.140919 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 5 | 5 | 100 | 0.0587742 | 0.20665 | 0.147876 | 0.0732639 |
| `-0.6--0.4` | 7 | 7 | 57 | 0.131389 | 0.426428 | 0.29504 | 0.193506 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
