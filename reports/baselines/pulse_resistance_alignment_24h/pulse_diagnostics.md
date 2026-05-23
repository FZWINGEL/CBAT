# PULSE Diagnostics

This is a PULSE resistance baseline diagnostic, not a multimodal claim.

## C-Rate Holdout

| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00194971 | 0.00490494 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00204864 | 0.00455986 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00214153 | 0.00454284 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P2_state_capacity` | 0.00229008 | 0.00518532 |
| `delta_pulse_1s_resistance` | `L1_ridge` | `P3_state_nominal` | 0.00231382 | 0.00512569 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.0026031 | 0.00612653 |
| `delta_pulse_1s_resistance` | `L1_ridge` | `P2_state_capacity` | 0.0029597 | 0.00646031 |
| `delta_pulse_1s_resistance` | `L1_ridge` | `P1_state_time` | 0.00297749 | 0.00630932 |

## Outputs

- `leaderboard.csv`
- `plots/pulse_target_coverage_by_split.csv`
