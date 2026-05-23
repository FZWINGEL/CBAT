# PULSE Diagnostics

This is a PULSE resistance baseline diagnostic, not a multimodal claim.

## C-Rate Holdout

| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 0.00460596 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.0021389 | 0.00481467 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P2_state_capacity` | 0.00219008 | 0.00491976 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00223862 | 0.00465924 |
| `delta_pulse_1s_resistance` | `L1_ridge` | `P3_state_nominal` | 0.00231349 | 0.00512131 |
| `delta_pulse_1s_resistance` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00260373 | 0.00602753 |
| `delta_pulse_1s_resistance` | `L1_ridge` | `P2_state_capacity` | 0.00296245 | 0.00646448 |
| `delta_pulse_1s_resistance` | `L1_ridge` | `P1_state_time` | 0.00297868 | 0.00631207 |

## Outputs

- `leaderboard.csv`
- `plots/pulse_target_coverage_by_split.csv`
