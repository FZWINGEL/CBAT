# Semi-Empirical Capacity Baseline Summary

These are interpretable ridge-style domain comparators, not neural or architecture baselines.

| Target | Split | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `delta_capacity_Ah` | `profile_holdout_fold` | `SE3_c_rate_interactions` | 0.0801121 | 0.228893 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `SE3_c_rate_interactions` | 0.08019 | 0.229769 |
| `delta_capacity_Ah` | `condition_fold` | `SE3_c_rate_interactions` | 0.0811292 | 0.36874 |
| `capacity_Ah_k1` | `condition_fold` | `SE3_c_rate_interactions` | 0.0811723 | 0.369035 |
| `delta_capacity_Ah` | `condition_fold` | `SE4_coupled_stress` | 0.0834455 | 0.371479 |
| `capacity_Ah_k1` | `condition_fold` | `SE4_coupled_stress` | 0.0834979 | 0.37183 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `SE1_calendar_cycling` | 0.0837475 | 0.259712 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `SE1_calendar_cycling` | 0.0837846 | 0.259746 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `SE0_time_efc` | 0.0879604 | 0.25756 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `SE0_time_efc` | 0.088005 | 0.257474 |
| `delta_capacity_Ah` | `profile_holdout_fold` | `SE4_coupled_stress` | 0.089093 | 0.231046 |
| `capacity_Ah_k1` | `profile_holdout_fold` | `SE4_coupled_stress` | 0.0892941 | 0.23195 |
