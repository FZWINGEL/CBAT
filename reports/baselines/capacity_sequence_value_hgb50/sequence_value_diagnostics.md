# Sequence Value Diagnostics

Positive gain means the candidate feature group has lower condition-mean MAE.

| Comparison | Target | Split | Mean gain | Positive rows | Rows |
|---|---|---|---:|---:|---:|
| `order_vs_aggregate` | `capacity_Ah_k1` | `c_rate_holdout_fold` | 0.00129804 | 1 | 1 |
| `order_vs_aggregate` | `capacity_Ah_k1` | `condition_fold` | -0.0011511 | 2 | 5 |
| `order_vs_aggregate` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.00447287 | 1 | 1 |
| `order_vs_aggregate` | `capacity_Ah_k1` | `temperature_holdout_fold` | 0.00287828 | 2 | 2 |
| `order_vs_aggregate` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | 0.000352212 | 2 | 3 |
| `order_vs_aggregate` | `delta_capacity_Ah` | `c_rate_holdout_fold` | -0.00328221 | 0 | 1 |
| `order_vs_aggregate` | `delta_capacity_Ah` | `condition_fold` | -0.00229155 | 1 | 5 |
| `order_vs_aggregate` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.00725751 | 1 | 1 |
| `order_vs_aggregate` | `delta_capacity_Ah` | `temperature_holdout_fold` | -0.00361401 | 1 | 2 |
| `order_vs_aggregate` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | -0.00197343 | 2 | 3 |
| `order_vs_shuffled` | `capacity_Ah_k1` | `c_rate_holdout_fold` | 0.00823437 | 1 | 1 |
| `order_vs_shuffled` | `capacity_Ah_k1` | `condition_fold` | -0.00111158 | 2 | 5 |
| `order_vs_shuffled` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.00400455 | 1 | 1 |
| `order_vs_shuffled` | `capacity_Ah_k1` | `temperature_holdout_fold` | 0.00450416 | 2 | 2 |
| `order_vs_shuffled` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | -9.98424e-05 | 1 | 3 |
| `order_vs_shuffled` | `delta_capacity_Ah` | `c_rate_holdout_fold` | -0.00348868 | 0 | 1 |
| `order_vs_shuffled` | `delta_capacity_Ah` | `condition_fold` | -0.000993328 | 2 | 5 |
| `order_vs_shuffled` | `delta_capacity_Ah` | `profile_holdout_fold` | -0.0114108 | 0 | 1 |
| `order_vs_shuffled` | `delta_capacity_Ah` | `temperature_holdout_fold` | -0.00227116 | 1 | 2 |
| `order_vs_shuffled` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | -0.00150906 | 2 | 3 |
| `order_plus_stress_vs_stress` | `capacity_Ah_k1` | `c_rate_holdout_fold` | -0.00551325 | 0 | 1 |
| `order_plus_stress_vs_stress` | `capacity_Ah_k1` | `condition_fold` | -0.00284581 | 0 | 5 |
| `order_plus_stress_vs_stress` | `capacity_Ah_k1` | `profile_holdout_fold` | 0.00496707 | 1 | 1 |
| `order_plus_stress_vs_stress` | `capacity_Ah_k1` | `temperature_holdout_fold` | -0.00242236 | 0 | 2 |
| `order_plus_stress_vs_stress` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | 0.0098235 | 3 | 3 |
| `order_plus_stress_vs_stress` | `delta_capacity_Ah` | `c_rate_holdout_fold` | -0.0045121 | 0 | 1 |
| `order_plus_stress_vs_stress` | `delta_capacity_Ah` | `condition_fold` | -0.00306976 | 1 | 5 |
| `order_plus_stress_vs_stress` | `delta_capacity_Ah` | `profile_holdout_fold` | 0.0107322 | 1 | 1 |
| `order_plus_stress_vs_stress` | `delta_capacity_Ah` | `temperature_holdout_fold` | -0.00399839 | 1 | 2 |
| `order_plus_stress_vs_stress` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | -0.00133525 | 1 | 3 |
