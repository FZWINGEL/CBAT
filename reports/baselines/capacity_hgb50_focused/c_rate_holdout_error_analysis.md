# C-Rate Holdout Error Analysis

This diagnostic focuses on the high-C-rate holdout conditions because the
bounded L0-L3 baseline report identified C-rate transfer as the hardest
split.

Diagnostic rows: `24`

## Worst Held-Out Conditions

| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |
|---|---:|---:|---|---:|---:|---|---:|---:|---:|
| `capacity_Ah_k1` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.276435 | 0.557172 | 0.280737 |
| `capacity_Ah_k1` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.247365 | 0.556422 | 0.309057 |
| `delta_capacity_Ah` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.193506 | 0.484002 | 0.290497 |
| `capacity_Ah_k1` | 20 | 0 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.176425 | 0.484002 | 0.307577 |
| `capacity_Ah_k1` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.154353 | 0.402438 | 0.248086 |
| `capacity_Ah_k1` | 60 | 40 | `approx_10_100` | 1.67 | 16 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.147409 | 0.266788 | 0.119379 |
| `delta_capacity_Ah` | 36 | 10 | `approx_10_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140919 | 0.557172 | 0.416253 |
| `delta_capacity_Ah` | 24 | 0 | `approx_10_100` | 1.67 | 4 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.140443 | 0.402438 | 0.261996 |
| `delta_capacity_Ah` | 32 | 10 | `approx_0_100` | 1.67 | 6 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.136856 | 0.556422 | 0.419566 |
| `capacity_Ah_k1` | 56 | 40 | `approx_0_100` | 1.67 | 13 | `L2_hist_gradient_boosting:F4_state_log_age_scalar` | 0.131056 | 0.303248 | 0.172192 |

## Grouped Summaries

### temperature

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0` | 6 | 3 | 38 | 0.132982 | 0.396189 | 0.263207 | 0.193506 |
| `10` | 6 | 3 | 54 | 0.154004 | 0.474212 | 0.320208 | 0.276435 |
| `25` | 6 | 3 | 88 | 0.0683799 | 0.243851 | 0.175471 | 0.108527 |
| `40` | 6 | 3 | 134 | 0.097272 | 0.225164 | 0.127892 | 0.147409 |

### voltage_window_family

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `approx_0_100` | 8 | 4 | 62 | 0.146666 | 0.43965 | 0.292984 | 0.247365 |
| `approx_10_100` | 8 | 4 | 72 | 0.135481 | 0.347829 | 0.212347 | 0.276435 |
| `approx_10_90` | 8 | 4 | 180 | 0.0573315 | 0.217083 | 0.159752 | 0.0810477 |

### target

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | 12 | 12 | 157 | 0.125186 | 0.334854 | 0.209668 | 0.276435 |
| `delta_capacity_Ah` | 12 | 12 | 157 | 0.101133 | 0.334854 | 0.233721 | 0.193506 |

### parameter_set

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20` | 2 | 1 | 12 | 0.184965 | 0.484002 | 0.299037 | 0.193506 |
| `24` | 2 | 1 | 8 | 0.147398 | 0.402438 | 0.255041 | 0.154353 |
| `28` | 2 | 1 | 18 | 0.0665825 | 0.302125 | 0.235542 | 0.0810477 |
| `32` | 2 | 1 | 12 | 0.19211 | 0.556422 | 0.364311 | 0.247365 |
| `36` | 2 | 1 | 12 | 0.208677 | 0.557172 | 0.348495 | 0.276435 |
| `40` | 2 | 1 | 30 | 0.0612261 | 0.309043 | 0.247817 | 0.0732639 |
| `44` | 2 | 1 | 12 | 0.102527 | 0.414928 | 0.312402 | 0.108527 |
| `48` | 2 | 1 | 20 | 0.0479431 | 0.164916 | 0.116973 | 0.0589442 |
| `52` | 2 | 1 | 56 | 0.0546697 | 0.151708 | 0.0970387 | 0.0590889 |
| `56` | 2 | 1 | 26 | 0.107061 | 0.303248 | 0.196187 | 0.131056 |
| `60` | 2 | 1 | 32 | 0.137907 | 0.266788 | 0.128881 | 0.147409 |
| `64` | 2 | 1 | 76 | 0.0468477 | 0.105457 | 0.0586094 | 0.0504568 |

### interval_count_bucket

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `11-20` | 6 | 3 | 88 | 0.102065 | 0.293026 | 0.190962 | 0.147409 |
| `6-10` | 12 | 6 | 86 | 0.133801 | 0.413261 | 0.27946 | 0.276435 |
| `<=5` | 2 | 1 | 8 | 0.147398 | 0.402438 | 0.255041 | 0.154353 |
| `>20` | 4 | 2 | 132 | 0.0507587 | 0.128583 | 0.077824 | 0.0590889 |

### capacity_Ah_k_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.4-2.6` | 2 | 1 | 18 | 0.0665825 | 0.302125 | 0.235542 | 0.0810477 |
| `2.6-2.8` | 10 | 5 | 78 | 0.135896 | 0.382205 | 0.24631 | 0.247365 |
| `<2.4` | 8 | 4 | 194 | 0.0751627 | 0.208249 | 0.133086 | 0.147409 |
| `>=2.8` | 4 | 2 | 24 | 0.155602 | 0.48605 | 0.330448 | 0.276435 |

### delta_capacity_Ah_range

| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `-0.4--0.2` | 10 | 5 | 200 | 0.0554538 | 0.20665 | 0.151196 | 0.0810477 |
| `-0.6--0.4` | 14 | 7 | 114 | 0.154378 | 0.426428 | 0.27205 | 0.276435 |


## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.
