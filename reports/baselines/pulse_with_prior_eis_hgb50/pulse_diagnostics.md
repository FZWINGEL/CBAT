# PULSE Diagnostics

This is a PULSE resistance baseline diagnostic, not a multimodal claim.

## C-Rate Holdout

| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00193709 | 0.00459522 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P_E1_nominal_eis` | 0.00196226 | 0.00463408 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00217244 | 0.00470153 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P_E2_log_age_eis` | 0.00222738 | 0.0045701 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P_E3_stress_eis` | 0.00236237 | 0.00475423 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P_E0_prior_eis` | 0.00309528 | 0.00635889 |

## Outputs

- `leaderboard.csv`
- `plots/pulse_target_coverage_by_split.csv`
