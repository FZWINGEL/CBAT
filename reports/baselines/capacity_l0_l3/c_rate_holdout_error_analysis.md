# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.318605 | 0.557172 | 0.238566 |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.316051 | 0.557172 | 0.241121 |
| `capacity_Ah_k1` | 28 | 0 | `approx_10_90` | 1.67 | 9 | `L1_ridge:F3_state_nominal` | 0.299384 | 0.302125 | 0.00274042 |
| `delta_capacity_Ah` | 28 | 0 | `approx_10_90` | 1.67 | 9 | `L1_ridge:F3_state_nominal` | 0.295309 | 0.302125 | 0.00681635 |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L1_ridge:F3_state_nominal` | 0.275543 | 0.266788 | -0.00875464 |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L1_ridge:F3_state_nominal` | 0.267472 | 0.266788 | -0.000683992 |
| `capacity_Ah_k1` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.199195 | 0.414928 | 0.215734 |
| `delta_capacity_Ah` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.194536 | 0.414928 | 0.220393 |
| `delta_capacity_Ah` | 52 | 25 | `approx_10_90` | 1.67 | 28 | `L1_ridge:F3_state_nominal` | 0.165872 | 0.151708 | -0.0141637 |
| `capacity_Ah_k1` | 48 | 25 | `approx_10_100` | 1.67 | 10 | `L1_ridge:F3_state_nominal` | 0.163617 | 0.164916 | 0.00129914 |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.154384 | 0.396189 | 0.241804 | 0.299384 |
| `10` | 6 | 3 | 54 | 0.184226 | 0.474212 | 0.289986 | 0.318605 |
| `25` | 6 | 3 | 88 | 0.173951 | 0.243851 | 0.0699002 | 0.199195 |
| `40` | 6 | 3 | 134 | 0.189373 | 0.225164 | 0.0357917 | 0.275543 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.139979 | 0.43965 | 0.299671 | 0.199195 |
| `approx_10_100` | 8 | 4 | 72 | 0.202378 | 0.347829 | 0.145451 | 0.318605 |
| `approx_10_90` | 8 | 4 | 180 | 0.184093 | 0.217083 | 0.0329901 | 0.299384 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.175561 | 0.334854 | 0.159293 | 0.318605 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.175406 | 0.334854 | 0.159448 | 0.316051 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.106102 | 0.484002 | 0.3779 | 0.10813 |
| `24` | 2 | 1 | 8 | 0.0597034 | 0.402438 | 0.342735 | 0.061411 |
| `28` | 2 | 1 | 18 | 0.297347 | 0.302125 | 0.00477838 | 0.299384 |
| `32` | 2 | 1 | 12 | 0.102381 | 0.556422 | 0.454041 | 0.105354 |
| `36` | 2 | 1 | 12 | 0.317328 | 0.557172 | 0.239844 | 0.318605 |
| `40` | 2 | 1 | 30 | 0.132969 | 0.309043 | 0.176074 | 0.134916 |
| `44` | 2 | 1 | 12 | 0.196865 | 0.414928 | 0.218063 | 0.199195 |
| `48` | 2 | 1 | 20 | 0.160972 | 0.164916 | 0.00394386 | 0.163617 |
| `52` | 2 | 1 | 56 | 0.164015 | 0.151708 | -0.0123063 | 0.165872 |
| `56` | 2 | 1 | 26 | 0.154568 | 0.303248 | 0.148681 | 0.160184 |
| `60` | 2 | 1 | 32 | 0.271507 | 0.266788 | -0.00471932 | 0.275543 |
| `64` | 2 | 1 | 76 | 0.142043 | 0.105457 | -0.036586 | 0.144368 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.186348 | 0.293026 | 0.106679 | 0.275543 |
| `6-10` | 12 | 6 | 86 | 0.196833 | 0.413261 | 0.216428 | 0.318605 |
| `<=5` | 2 | 1 | 8 | 0.0597034 | 0.402438 | 0.342735 | 0.061411 |
| `>20` | 4 | 2 | 132 | 0.153029 | 0.128583 | -0.0244462 | 0.165872 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.297347 | 0.302125 | 0.00477838 | 0.299384 |
| `2.6-2.8` | 10 | 5 | 78 | 0.116745 | 0.382205 | 0.26546 | 0.163617 |
| `<2.4` | 8 | 4 | 194 | 0.177633 | 0.208249 | 0.0306157 | 0.275543 |
| `>=2.8` | 4 | 2 | 24 | 0.257097 | 0.48605 | 0.228953 | 0.318605 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.179469 | 0.20665 | 0.0271809 | 0.299384 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.172636 | 0.426428 | 0.253792 | 0.318605 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
