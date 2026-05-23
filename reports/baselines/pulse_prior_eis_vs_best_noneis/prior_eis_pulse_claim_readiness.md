# Prior-EIS Pulse Claim Readiness

This report compares prior-EIS feature groups against the strongest supplied non-EIS groups on the same EIS-covered prediction population.
It does not authorize broad EIS, DRT, embedding, neural, CBAT, or multimodal claims.

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| Prior EIS beats strongest non-EIS for pulse primary target | `supported` | 1 split rows have bootstrap p05 > 0; C-rate mean -9.39059e-05, p05 -0.000185681 | Allow only narrow split-specific EIS claim |
| Leakage safety | `supported` | Only prior EIS `k` scalar features are allowed for non-EIS targets. | Future EIS state, EIS deltas, R0/R1, DRT, and embeddings remain blocked. |

## Paired Gain Summary

| Target | Split | Prior-EIS group | Non-EIS group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `delta_pulse_1s_resistance` | `c_rate_holdout_fold` | `P_E1_nominal_eis` | `P3_state_nominal` | 12 | -9.39059e-05 | -0.000185681 | -8.53293e-05 | -1.34657e-05 | 0.166667 |
| `delta_pulse_1s_resistance` | `condition_fold` | `P_E3_stress_eis` | `P5_stress_v1_1` | 76 | 1.3029e-05 | -2.76377e-05 | 1.2344e-05 | 5.64545e-05 | 0.592105 |
| `delta_pulse_1s_resistance` | `profile_holdout_fold` | `P_E1_nominal_eis` | `P3_state_nominal` | 12 | 3.06805e-05 | 1.27532e-06 | 3.11119e-05 | 6.14918e-05 | 0.833333 |
| `delta_pulse_1s_resistance` | `temperature_holdout_fold` | `P_E3_stress_eis` | `P5_stress_v1_1` | 38 | 2.47078e-05 | -1.46554e-05 | 2.35321e-05 | 6.88098e-05 | 0.578947 |
| `delta_pulse_1s_resistance` | `voltage_window_holdout_fold` | `P_E1_nominal_eis` | `P1_state_time` | 76 | -7.74487e-05 | -0.000233144 | -7.17909e-05 | 6.18443e-05 | 0.618421 |
