# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:C_P3_stress_pulse` | 0.258614 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:C_P3_stress_pulse` | 0.229108 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:C_P3_stress_pulse` | 0.209102 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.186708 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:C_P3_stress_pulse` | 0.153379 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.146894 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140928 | reference_missing | reference_missing |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:C_P3_stress_pulse` | 0.13536 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.129079 | reference_missing | reference_missing |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.120832 | reference_missing | reference_missing |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.138135 | NA | NA | 0.209102 |
| `10` | 6 | 3 | 54 | 0.147375 | NA | NA | 0.258614 |
| `25` | 6 | 3 | 88 | 0.0664055 | NA | NA | 0.111287 |
| `40` | 6 | 3 | 134 | 0.0839789 | NA | NA | 0.13536 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.139433 | NA | NA | 0.229108 |
| `approx_10_100` | 8 | 4 | 72 | 0.132205 | NA | NA | 0.258614 |
| `approx_10_90` | 8 | 4 | 180 | 0.0552834 | NA | NA | 0.0877415 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.120213 | NA | NA | 0.258614 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.0977347 | NA | NA | 0.186708 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.197905 | NA | NA | 0.209102 |
| `24` | 2 | 1 | 8 | 0.147153 | NA | NA | 0.153379 |
| `28` | 2 | 1 | 18 | 0.0693477 | NA | NA | 0.0877415 |
| `32` | 2 | 1 | 12 | 0.179094 | NA | NA | 0.229108 |
| `36` | 2 | 1 | 12 | 0.202754 | NA | NA | 0.258614 |
| `40` | 2 | 1 | 30 | 0.0602776 | NA | NA | 0.0769647 |
| `44` | 2 | 1 | 12 | 0.0991473 | NA | NA | 0.111287 |
| `48` | 2 | 1 | 20 | 0.0508165 | NA | NA | 0.0564573 |
| `52` | 2 | 1 | 56 | 0.0492526 | NA | NA | 0.0558223 |
| `56` | 2 | 1 | 26 | 0.0815854 | NA | NA | 0.0936668 |
| `60` | 2 | 1 | 32 | 0.128096 | NA | NA | 0.13536 |
| `64` | 2 | 1 | 76 | 0.0422556 | NA | NA | 0.0516656 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.0899862 | NA | NA | 0.13536 |
| `6-10` | 12 | 6 | 86 | 0.133177 | NA | NA | 0.258614 |
| `<=5` | 2 | 1 | 8 | 0.147153 | NA | NA | 0.153379 |
| `>20` | 4 | 2 | 132 | 0.0457541 | NA | NA | 0.0558223 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.0693477 | NA | NA | 0.0877415 |
| `2.6-2.8` | 10 | 5 | 78 | 0.131311 | NA | NA | 0.229108 |
| `<2.4` | 8 | 4 | 194 | 0.0699704 | NA | NA | 0.13536 |
| `>=2.8` | 4 | 2 | 24 | 0.150951 | NA | NA | 0.258614 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.05439 | NA | NA | 0.0877415 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.147962 | NA | NA | 0.258614 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
