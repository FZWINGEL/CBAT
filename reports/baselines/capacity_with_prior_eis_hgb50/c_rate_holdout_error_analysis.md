# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.251486 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.221326 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.213158 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.18183 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.177175 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.146931 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.14261 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.127725 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.122134 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.120723 | reference_missing | reference_missing |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.139169 | NA | NA | 0.213158 |
| `10` | 6 | 3 | 54 | 0.14414 | NA | NA | 0.251486 |
| `25` | 6 | 3 | 88 | 0.0688777 | NA | NA | 0.110773 |
| `40` | 6 | 3 | 134 | 0.0872135 | NA | NA | 0.14261 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.140606 | NA | NA | 0.221326 |
| `approx_10_100` | 8 | 4 | 72 | 0.132653 | NA | NA | 0.251486 |
| `approx_10_90` | 8 | 4 | 180 | 0.0562915 | NA | NA | 0.0995198 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.123572 | NA | NA | 0.251486 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.096128 | NA | NA | 0.18183 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.197494 | NA | NA | 0.213158 |
| `24` | 2 | 1 | 8 | 0.148949 | NA | NA | 0.177175 |
| `28` | 2 | 1 | 18 | 0.0710654 | NA | NA | 0.0995198 |
| `32` | 2 | 1 | 12 | 0.174526 | NA | NA | 0.221326 |
| `36` | 2 | 1 | 12 | 0.199209 | NA | NA | 0.251486 |
| `40` | 2 | 1 | 30 | 0.0586857 | NA | NA | 0.0641596 |
| `44` | 2 | 1 | 12 | 0.104081 | NA | NA | 0.110773 |
| `48` | 2 | 1 | 20 | 0.0500809 | NA | NA | 0.0601676 |
| `52` | 2 | 1 | 56 | 0.0524715 | NA | NA | 0.0548323 |
| `56` | 2 | 1 | 26 | 0.0863255 | NA | NA | 0.0875691 |
| `60` | 2 | 1 | 32 | 0.132372 | NA | NA | 0.14261 |
| `64` | 2 | 1 | 76 | 0.0429432 | NA | NA | 0.0499526 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.092461 | NA | NA | 0.14261 |
| `6-10` | 12 | 6 | 86 | 0.132743 | NA | NA | 0.251486 |
| `<=5` | 2 | 1 | 8 | 0.148949 | NA | NA | 0.177175 |
| `>20` | 4 | 2 | 132 | 0.0477074 | NA | NA | 0.0548323 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.0710654 | NA | NA | 0.0995198 |
| `2.6-2.8` | 10 | 5 | 78 | 0.131475 | NA | NA | 0.221326 |
| `<2.4` | 8 | 4 | 194 | 0.0716181 | NA | NA | 0.14261 |
| `>=2.8` | 4 | 2 | 24 | 0.151645 | NA | NA | 0.251486 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.0550494 | NA | NA | 0.0995198 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.148994 | NA | NA | 0.251486 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
