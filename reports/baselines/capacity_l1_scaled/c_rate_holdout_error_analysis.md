# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.314623 | 0.557172 | 0.242549 |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.314368 | 0.557172 | 0.242804 |
| `capacity_Ah_k1` | 28 | 0 | `approx_10_90` | 1.67 | 9 | `L1_ridge:F3_state_nominal` | 0.294517 | 0.302125 | 0.00760781 |
| `delta_capacity_Ah` | 28 | 0 | `approx_10_90` | 1.67 | 9 | `L1_ridge:F3_state_nominal` | 0.294089 | 0.302125 | 0.00803541 |
| `delta_capacity_Ah` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L1_ridge:F3_state_nominal` | 0.283029 | 0.266788 | -0.0162415 |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L1_ridge:F3_state_nominal` | 0.282209 | 0.266788 | -0.0154208 |
| `capacity_Ah_k1` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.192494 | 0.414928 | 0.222434 |
| `delta_capacity_Ah` | 44 | 25 | `approx_0_100` | 1.67 | 6 | `L1_ridge:F3_state_nominal` | 0.192024 | 0.414928 | 0.222904 |
| `delta_capacity_Ah` | 52 | 25 | `approx_10_90` | 1.67 | 28 | `L1_ridge:F3_state_nominal` | 0.171288 | 0.151708 | -0.0195799 |
| `capacity_Ah_k1` | 52 | 25 | `approx_10_90` | 1.67 | 28 | `L1_ridge:F3_state_nominal` | 0.170675 | 0.151708 | -0.0189664 |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.157759 | 0.396189 | 0.238429 | 0.294517 |
| `10` | 6 | 3 | 54 | 0.184586 | 0.474212 | 0.289626 | 0.314623 |
| `25` | 6 | 3 | 88 | 0.173513 | 0.243851 | 0.0703376 | 0.192494 |
| `40` | 6 | 3 | 134 | 0.192217 | 0.225164 | 0.0329475 | 0.283029 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.13824 | 0.43965 | 0.30141 | 0.192494 |
| `approx_10_100` | 8 | 4 | 72 | 0.205652 | 0.347829 | 0.142176 | 0.314623 |
| `approx_10_90` | 8 | 4 | 180 | 0.187165 | 0.217083 | 0.0299185 | 0.294517 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.176993 | 0.334854 | 0.157861 | 0.314623 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.177045 | 0.334854 | 0.157809 | 0.314368 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.110779 | 0.484002 | 0.373223 | 0.110978 |
| `24` | 2 | 1 | 8 | 0.0681956 | 0.402438 | 0.334243 | 0.0683692 |
| `28` | 2 | 1 | 18 | 0.294303 | 0.302125 | 0.00782161 | 0.294517 |
| `32` | 2 | 1 | 12 | 0.106093 | 0.556422 | 0.450329 | 0.106407 |
| `36` | 2 | 1 | 12 | 0.314495 | 0.557172 | 0.242677 | 0.314623 |
| `40` | 2 | 1 | 30 | 0.133171 | 0.309043 | 0.175872 | 0.133228 |
| `44` | 2 | 1 | 12 | 0.192259 | 0.414928 | 0.222669 | 0.192494 |
| `48` | 2 | 1 | 20 | 0.157299 | 0.164916 | 0.00761669 | 0.157566 |
| `52` | 2 | 1 | 56 | 0.170982 | 0.151708 | -0.0192731 | 0.171288 |
| `56` | 2 | 1 | 26 | 0.143828 | 0.303248 | 0.15942 | 0.144395 |
| `60` | 2 | 1 | 32 | 0.282619 | 0.266788 | -0.0158311 | 0.283029 |
| `64` | 2 | 1 | 76 | 0.150203 | 0.105457 | -0.0447464 | 0.150468 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.186539 | 0.293026 | 0.106487 | 0.283029 |
| `6-10` | 12 | 6 | 86 | 0.195871 | 0.413261 | 0.217389 | 0.314623 |
| `<=5` | 2 | 1 | 8 | 0.0681956 | 0.402438 | 0.334243 | 0.0683692 |
| `>20` | 4 | 2 | 132 | 0.160592 | 0.128583 | -0.0320098 | 0.171288 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.294303 | 0.302125 | 0.00782161 | 0.294517 |
| `2.6-2.8` | 10 | 5 | 78 | 0.117239 | 0.382205 | 0.264966 | 0.157566 |
| `<2.4` | 8 | 4 | 194 | 0.184244 | 0.208249 | 0.0240053 | 0.283029 |
| `>=2.8` | 4 | 2 | 24 | 0.253377 | 0.48605 | 0.232673 | 0.314623 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.181192 | 0.20665 | 0.0254582 | 0.294517 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.174038 | 0.426428 | 0.25239 | 0.314623 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
