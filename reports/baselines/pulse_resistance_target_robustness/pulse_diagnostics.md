# PULSE Diagnostics

This is a PULSE resistance baseline diagnostic, not a multimodal claim.

## C-Rate Holdout

| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `pulse_10ms_resistance_k1` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00179792 | 0.00406398 |
| `delta_pulse_10ms_resistance` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00180642 | 0.00449567 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 0.00460596 |
| `pulse_1s_resistance_k1` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00189616 | 0.0043168 |
| `pulse_10ms_resistance_k1` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00193363 | 0.00436169 |
| `delta_pulse_10ms_resistance` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00195699 | 0.00418844 |
| `pulse_10ms_resistance_k1` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00198445 | 0.00444664 |
| `delta_pulse_10ms_resistance` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00202926 | 0.00441087 |

## Outputs

- `leaderboard.csv`
- `plots/pulse_target_coverage_by_split.csv`
