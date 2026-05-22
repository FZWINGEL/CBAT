# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `12`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.193506 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140919 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140443 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.136856 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.128406 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0965265 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 56 | 40 | `approx_0_100` | 1.67 | 13 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0830665 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 40 | 10 | `approx_10_90` | 1.67 | 15 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0732639 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 52 | 25 | `approx_10_90` | 1.67 | 28 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0590889 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 48 | 25 | `approx_10_100` | 1.67 | 10 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.0589442 | reference_missing | reference_missing |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 3 | 3 | 19 | 0.128689 | NA | NA | 0.193506 |
| `10` | 3 | 3 | 27 | 0.117013 | NA | NA | 0.140919 |
| `25` | 3 | 3 | 44 | 0.0715198 | NA | NA | 0.0965265 |
| `40` | 3 | 3 | 67 | 0.0873096 | NA | NA | 0.128406 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 4 | 4 | 31 | 0.127489 | NA | NA | 0.193506 |
| `approx_10_100` | 4 | 4 | 36 | 0.117178 | NA | NA | 0.140919 |
| `approx_10_90` | 4 | 4 | 90 | 0.0587317 | NA | NA | 0.0732639 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.101133 | NA | NA | 0.193506 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 1 | 1 | 6 | 0.193506 | NA | NA | 0.193506 |
| `24` | 1 | 1 | 4 | 0.140443 | NA | NA | 0.140443 |
| `28` | 1 | 1 | 9 | 0.0521174 | NA | NA | 0.0521174 |
| `32` | 1 | 1 | 6 | 0.136856 | NA | NA | 0.136856 |
| `36` | 1 | 1 | 6 | 0.140919 | NA | NA | 0.140919 |
| `40` | 1 | 1 | 15 | 0.0732639 | NA | NA | 0.0732639 |
| `44` | 1 | 1 | 6 | 0.0965265 | NA | NA | 0.0965265 |
| `48` | 1 | 1 | 10 | 0.0589442 | NA | NA | 0.0589442 |
| `52` | 1 | 1 | 28 | 0.0590889 | NA | NA | 0.0590889 |
| `56` | 1 | 1 | 13 | 0.0830665 | NA | NA | 0.0830665 |
| `60` | 1 | 1 | 16 | 0.128406 | NA | NA | 0.128406 |
| `64` | 1 | 1 | 38 | 0.0504568 | NA | NA | 0.0504568 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 3 | 3 | 44 | 0.094912 | NA | NA | 0.128406 |
| `6-10` | 6 | 6 | 43 | 0.113145 | NA | NA | 0.193506 |
| `<=5` | 1 | 1 | 4 | 0.140443 | NA | NA | 0.140443 |
| `>20` | 2 | 2 | 66 | 0.0547728 | NA | NA | 0.0590889 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 1 | 1 | 9 | 0.0521174 | NA | NA | 0.0521174 |
| `2.6-2.8` | 5 | 5 | 39 | 0.122563 | NA | NA | 0.193506 |
| `<2.4` | 4 | 4 | 97 | 0.0778038 | NA | NA | 0.128406 |
| `>=2.8` | 2 | 2 | 12 | 0.118723 | NA | NA | 0.140919 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 5 | 5 | 100 | 0.0587742 | NA | NA | 0.0732639 |
| `-0.6--0.4` | 7 | 7 | 57 | 0.131389 | NA | NA | 0.193506 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
