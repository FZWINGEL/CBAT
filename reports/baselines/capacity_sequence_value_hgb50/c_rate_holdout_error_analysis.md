# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.253991 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.230332 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.191864 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F16_event_order_shuffled` | 0.181473 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.167332 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.1494 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F16_event_order_shuffled` | 0.135184 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F16_event_order_shuffled` | 0.131233 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.125066 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F16_event_order_shuffled` | 0.124145 | reference_missing | reference_missing |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.13438 | NA | NA | 0.191864 |
| `10` | 6 | 3 | 54 | 0.144319 | NA | NA | 0.253991 |
| `25` | 6 | 3 | 88 | 0.0708639 | NA | NA | 0.125066 |
| `40` | 6 | 3 | 134 | 0.0858353 | NA | NA | 0.1494 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.137491 | NA | NA | 0.230332 |
| `approx_10_100` | 8 | 4 | 72 | 0.131521 | NA | NA | 0.253991 |
| `approx_10_90` | 8 | 4 | 180 | 0.0575365 | NA | NA | 0.0765218 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.122442 | NA | NA | 0.253991 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.0952571 | NA | NA | 0.181473 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.186668 | NA | NA | 0.191864 |
| `24` | 2 | 1 | 8 | 0.151258 | NA | NA | 0.167332 |
| `28` | 2 | 1 | 18 | 0.065215 | NA | NA | 0.0765218 |
| `32` | 2 | 1 | 12 | 0.177239 | NA | NA | 0.230332 |
| `36` | 2 | 1 | 12 | 0.192612 | NA | NA | 0.253991 |
| `40` | 2 | 1 | 30 | 0.0631054 | NA | NA | 0.0759613 |
| `44` | 2 | 1 | 12 | 0.106867 | NA | NA | 0.125066 |
| `48` | 2 | 1 | 20 | 0.0485605 | NA | NA | 0.0552521 |
| `52` | 2 | 1 | 56 | 0.0571644 | NA | NA | 0.0581341 |
| `56` | 2 | 1 | 26 | 0.0791901 | NA | NA | 0.0907798 |
| `60` | 2 | 1 | 32 | 0.133655 | NA | NA | 0.1494 |
| `64` | 2 | 1 | 76 | 0.0446612 | NA | NA | 0.0536172 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.0919833 | NA | NA | 0.1494 |
| `6-10` | 12 | 6 | 86 | 0.129527 | NA | NA | 0.253991 |
| `<=5` | 2 | 1 | 8 | 0.151258 | NA | NA | 0.167332 |
| `>20` | 4 | 2 | 132 | 0.0509128 | NA | NA | 0.0581341 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.065215 | NA | NA | 0.0765218 |
| `2.6-2.8` | 10 | 5 | 78 | 0.128583 | NA | NA | 0.230332 |
| `<2.4` | 8 | 4 | 194 | 0.0746464 | NA | NA | 0.1494 |
| `>=2.8` | 4 | 2 | 24 | 0.14974 | NA | NA | 0.253991 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.0557413 | NA | NA | 0.0765218 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.146784 | NA | NA | 0.253991 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
