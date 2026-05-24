# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.276435 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.247365 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.193506 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.176425 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.154353 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.147409 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140919 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140443 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.136856 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 56 | 40 | `approx_0_100` | 1.67 | 13 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.131056 | reference_missing | reference_missing |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.132982 | NA | NA | 0.193506 |
| `10` | 6 | 3 | 54 | 0.154004 | NA | NA | 0.276435 |
| `25` | 6 | 3 | 88 | 0.0683799 | NA | NA | 0.108527 |
| `40` | 6 | 3 | 134 | 0.097272 | NA | NA | 0.147409 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.146666 | NA | NA | 0.247365 |
| `approx_10_100` | 8 | 4 | 72 | 0.135481 | NA | NA | 0.276435 |
| `approx_10_90` | 8 | 4 | 180 | 0.0573315 | NA | NA | 0.0810477 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.125186 | NA | NA | 0.276435 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.101133 | NA | NA | 0.193506 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.184965 | NA | NA | 0.193506 |
| `24` | 2 | 1 | 8 | 0.147398 | NA | NA | 0.154353 |
| `28` | 2 | 1 | 18 | 0.0665825 | NA | NA | 0.0810477 |
| `32` | 2 | 1 | 12 | 0.19211 | NA | NA | 0.247365 |
| `36` | 2 | 1 | 12 | 0.208677 | NA | NA | 0.276435 |
| `40` | 2 | 1 | 30 | 0.0612261 | NA | NA | 0.0732639 |
| `44` | 2 | 1 | 12 | 0.102527 | NA | NA | 0.108527 |
| `48` | 2 | 1 | 20 | 0.0479431 | NA | NA | 0.0589442 |
| `52` | 2 | 1 | 56 | 0.0546697 | NA | NA | 0.0590889 |
| `56` | 2 | 1 | 26 | 0.107061 | NA | NA | 0.131056 |
| `60` | 2 | 1 | 32 | 0.137907 | NA | NA | 0.147409 |
| `64` | 2 | 1 | 76 | 0.0468477 | NA | NA | 0.0504568 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.102065 | NA | NA | 0.147409 |
| `6-10` | 12 | 6 | 86 | 0.133801 | NA | NA | 0.276435 |
| `<=5` | 2 | 1 | 8 | 0.147398 | NA | NA | 0.154353 |
| `>20` | 4 | 2 | 132 | 0.0507587 | NA | NA | 0.0590889 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.0665825 | NA | NA | 0.0810477 |
| `2.6-2.8` | 10 | 5 | 78 | 0.135896 | NA | NA | 0.247365 |
| `<2.4` | 8 | 4 | 194 | 0.0751627 | NA | NA | 0.147409 |
| `>=2.8` | 4 | 2 | 24 | 0.155602 | NA | NA | 0.276435 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.0554538 | NA | NA | 0.0810477 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.154378 | NA | NA | 0.276435 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
