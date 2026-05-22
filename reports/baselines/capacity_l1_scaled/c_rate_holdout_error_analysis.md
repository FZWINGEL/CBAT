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

## Table

Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.
