# Replicate Uncertainty Summary

This is a condition-triplet diagnostic. It does not validate calibrated uncertainty.

| Target | Split | Model | Feature group | Mean model MAE | Mean replicate spread | Error > spread fraction |
|---|---|---|---|---:|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0445674 | 0.0474871 | 0.618421 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0485748 | 0.0532111 | 0.578947 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.053869 | 0.0728952 | 0.197368 |
| `delta_capacity_Ah` | `condition_fold` | `L3_quantile_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0555644 | 0.0474871 | 0.486842 |
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F3_state_nominal` | 0.0577807 | 0.0474871 | 0.631579 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F3_state_nominal` | 0.0587631 | 0.0728952 | 0.223684 |
| `delta_capacity_Ah` | `condition_fold` | `L3_quantile_hist_gradient_boosting` | `F3_state_nominal` | 0.0607556 | 0.0474871 | 0.513158 |
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F2_state_exposure` | 0.0610798 | 0.0474871 | 0.684211 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `F1_state_time` | 0.0621921 | 0.0749626 | 0.25 |
| `delta_capacity_Ah` | `condition_fold` | `L3_quantile_hist_gradient_boosting` | `F1_state_time` | 0.0645597 | 0.0474871 | 0.631579 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F2_state_exposure` | 0.0647348 | 0.0728952 | 0.276316 |
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F1_state_time` | 0.0647428 | 0.0474871 | 0.710526 |
