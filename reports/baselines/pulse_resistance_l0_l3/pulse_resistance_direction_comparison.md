# PULSE Direction Comparison

Direction-specific target extraction is diagnostic. `mean` remains the canonical target unless a later policy changes it.

| Direction | Split | Best model | Feature group | Condition mean MAE | Test rows | Status |
|---|---|---|---|---:|---:|---|
| `mean` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000960407 | 3751 | `passed` |
| `mean` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.0010961 | 1756 | `passed` |
| `mean` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 143 | `passed` |
| `mean` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000953406 | 733 | `passed` |
| `mean` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00117733 | 3751 | `passed` |
| `charge` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000960407 | 3751 | `passed` |
| `charge` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.0010961 | 1756 | `passed` |
| `charge` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 143 | `passed` |
| `charge` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000953406 | 733 | `passed` |
| `charge` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00117733 | 3751 | `passed` |
| `discharge` | `none` | `none` | `none` | no_metrics | 0 | `warning` |
