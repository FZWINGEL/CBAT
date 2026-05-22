# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `36`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `delta_capacity_per_efc_target` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.614094 | reference_missing | reference_missing |
| `delta_capacity_per_efc_target` | 52 | 25 | `approx_10_90` | 1.67 | 28 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.346969 | reference_missing | reference_missing |
| `delta_capacity_per_efc_target` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.333494 | reference_missing | reference_missing |
| `delta_capacity_per_efc_target` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.312404 | reference_missing | reference_missing |
| `delta_capacity_per_efc_target` | 56 | 40 | `approx_0_100` | 1.67 | 13 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.303631 | reference_missing | reference_missing |
| `delta_capacity_per_efc_target` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.245535 | reference_missing | reference_missing |
| `delta_capacity_per_day_target` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.236558 | reference_missing | reference_missing |
| `delta_capacity_per_day_target` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.230231 | reference_missing | reference_missing |
| `delta_capacity_per_day_target` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F8_timestamp_weighted_stress` | 0.204101 | reference_missing | reference_missing |
| `delta_capacity_per_efc_target` | 64 | 40 | `approx_10_90` | 1.67 | 38 | `L2_hist_gradient_boosting:F12_voltage_cold_current_interactions` | 0.196845 | reference_missing | reference_missing |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 9 | 3 | 57 | 0.191127 | NA | NA | 0.614094 |
| `10` | 9 | 3 | 81 | 0.177483 | NA | NA | 0.333494 |
| `25` | 9 | 3 | 132 | 0.110932 | NA | NA | 0.346969 |
| `40` | 9 | 3 | 201 | 0.135314 | NA | NA | 0.303631 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 12 | 4 | 93 | 0.178472 | NA | NA | 0.312404 |
| `approx_10_100` | 12 | 4 | 108 | 0.183111 | NA | NA | 0.614094 |
| `approx_10_90` | 12 | 4 | 270 | 0.0995592 | NA | NA | 0.346969 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.101133 | NA | NA | 0.193506 |
| `delta_capacity_per_day_target` | 12 | 12 | 157 | 0.121271 | NA | NA | 0.236558 |
| `delta_capacity_per_efc_target` | 12 | 12 | 157 | 0.238739 | NA | NA | 0.614094 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 3 | 1 | 18 | 0.18568 | NA | NA | 0.245535 |
| `24` | 3 | 1 | 12 | 0.328256 | NA | NA | 0.614094 |
| `28` | 3 | 1 | 27 | 0.0594454 | NA | NA | 0.0656167 |
| `32` | 3 | 1 | 18 | 0.228606 | NA | NA | 0.312404 |
| `36` | 3 | 1 | 18 | 0.210211 | NA | NA | 0.333494 |
| `40` | 3 | 1 | 45 | 0.0936333 | NA | NA | 0.123122 |
| `44` | 3 | 1 | 18 | 0.12487 | NA | NA | 0.204101 |
| `48` | 3 | 1 | 30 | 0.054112 | NA | NA | 0.0735988 |
| `52` | 3 | 1 | 84 | 0.153815 | NA | NA | 0.346969 |
| `56` | 3 | 1 | 39 | 0.174732 | NA | NA | 0.303631 |
| `60` | 3 | 1 | 48 | 0.139865 | NA | NA | 0.17557 |
| `64` | 3 | 1 | 114 | 0.0913435 | NA | NA | 0.196845 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 9 | 3 | 132 | 0.136077 | NA | NA | 0.303631 |
| `6-10` | 18 | 6 | 129 | 0.143821 | NA | NA | 0.333494 |
| `<=5` | 3 | 1 | 12 | 0.328256 | NA | NA | 0.614094 |
| `>20` | 6 | 2 | 198 | 0.122579 | NA | NA | 0.346969 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 3 | 1 | 27 | 0.0594454 | NA | NA | 0.0656167 |
| `2.6-2.8` | 15 | 5 | 117 | 0.194277 | NA | NA | 0.614094 |
| `<2.4` | 12 | 4 | 291 | 0.119664 | NA | NA | 0.346969 |
| `>=2.8` | 6 | 2 | 36 | 0.16754 | NA | NA | 0.333494 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 15 | 5 | 300 | 0.0904697 | NA | NA | 0.346969 |
| `-0.6--0.4` | 21 | 7 | 171 | 0.198889 | NA | NA | 0.614094 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
