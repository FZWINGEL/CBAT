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

## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
