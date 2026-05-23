# PULSE Alignment Robustness

| Threshold | Split | Best model | Feature group | Condition mean MAE | Worst condition MAE | Test rows |
|---|---|---|---|---:|---:|---:|
| `all` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 0.00460596 | 143 |
| `all` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000960407 | 0.00357084 | 3751 |
| `all` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000953406 | 0.00278087 | 733 |
| `all` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.0010961 | 0.00437046 | 1756 |
| `all` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00117733 | 0.00517459 | 3751 |
| `24h` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00194971 | 0.00490494 | 143 |
| `24h` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000952007 | 0.00350566 | 3748 |
| `24h` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000943296 | 0.00281563 | 733 |
| `24h` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00109608 | 0.00432848 | 1756 |
| `24h` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00117415 | 0.00507492 | 3748 |
| `36h` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 0.00460596 | 143 |
| `36h` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000960407 | 0.00357084 | 3751 |
| `36h` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000953406 | 0.00278087 | 733 |
| `36h` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.0010961 | 0.00437046 | 1756 |
| `36h` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00117733 | 0.00517459 | 3751 |

Decision: 24h filtering preserves C-rate/profile row counts but slightly worsens C-rate MAE; 36h matches all finite canonical rows for the current target table. Alignment remains a reporting sensitivity, not a canonical exclusion policy.
