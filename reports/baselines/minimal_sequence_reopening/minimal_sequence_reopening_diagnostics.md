# Minimal Sequence Reopening Diagnostics

Positive gain means the true-sequence candidate has lower condition-mean MAE.

| Comparison | Target | Split | Model | Mean gain | Positive rows | Rows |
|---|---|---|---|---:|---:|---:|
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `S0_ridge_true_sequence` | 0.371281 | 1 | 1 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `S2_torch_mlp_true_sequence` | 1.6569 | 1 | 1 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `condition_fold` | `S0_ridge_true_sequence` | -0.00497486 | 2 | 5 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `condition_fold` | `S2_torch_mlp_true_sequence` | 0.148243 | 5 | 5 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `profile_holdout_fold` | `S0_ridge_true_sequence` | -0.344478 | 0 | 1 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `profile_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.408122 | 0 | 1 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `temperature_holdout_fold` | `S0_ridge_true_sequence` | -0.00764117 | 1 | 2 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `temperature_holdout_fold` | `S2_torch_mlp_true_sequence` | 0.203811 | 2 | 2 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `S0_ridge_true_sequence` | -0.138544 | 1 | 3 |
| `true_sequence_vs_shuffled` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.0586134 | 1 | 3 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `S0_ridge_true_sequence` | 0.370538 | 1 | 1 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.0233347 | 0 | 1 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `condition_fold` | `S0_ridge_true_sequence` | -0.00524284 | 2 | 5 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `condition_fold` | `S2_torch_mlp_true_sequence` | 0.0144742 | 4 | 5 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `profile_holdout_fold` | `S0_ridge_true_sequence` | -0.330054 | 0 | 1 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `profile_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.00830753 | 0 | 1 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `temperature_holdout_fold` | `S0_ridge_true_sequence` | -0.00704933 | 1 | 2 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `temperature_holdout_fold` | `S2_torch_mlp_true_sequence` | 0.0359511 | 2 | 2 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `S0_ridge_true_sequence` | -0.139149 | 1 | 3 |
| `true_sequence_vs_shuffled` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.0309728 | 1 | 3 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `S0_ridge_true_sequence` | -0.203677 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.856378 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `condition_fold` | `S0_ridge_true_sequence` | -0.0657137 | 0 | 5 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `condition_fold` | `S2_torch_mlp_true_sequence` | -0.245039 | 0 | 5 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `profile_holdout_fold` | `S0_ridge_true_sequence` | -0.376352 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `profile_holdout_fold` | `S2_torch_mlp_true_sequence` | -1.04196 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `temperature_holdout_fold` | `S0_ridge_true_sequence` | -0.107865 | 0 | 2 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `temperature_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.477205 | 0 | 2 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `S0_ridge_true_sequence` | -0.192252 | 0 | 3 |
| `true_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.569106 | 0 | 3 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `S0_ridge_true_sequence` | -0.243676 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.415457 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `condition_fold` | `S0_ridge_true_sequence` | -0.0767735 | 0 | 5 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `condition_fold` | `S2_torch_mlp_true_sequence` | -0.0908392 | 0 | 5 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `profile_holdout_fold` | `S0_ridge_true_sequence` | -0.347592 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `profile_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.0693494 | 0 | 1 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `temperature_holdout_fold` | `S0_ridge_true_sequence` | -0.126284 | 0 | 2 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `temperature_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.092382 | 0 | 2 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `S0_ridge_true_sequence` | -0.209892 | 0 | 3 |
| `true_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.147979 | 0 | 3 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `S0_ridge_true_sequence` | -0.212808 | 0 | 1 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.86551 | 0 | 1 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `condition_fold` | `S0_ridge_true_sequence` | -0.0668968 | 0 | 5 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `condition_fold` | `S2_torch_mlp_true_sequence` | -0.246222 | 0 | 5 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `temperature_holdout_fold` | `S0_ridge_true_sequence` | -0.11464 | 0 | 2 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `temperature_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.48398 | 0 | 2 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `S0_ridge_true_sequence` | -0.116328 | 0 | 3 |
| `true_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.493182 | 0 | 3 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `S0_ridge_true_sequence` | -0.236624 | 0 | 1 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.408404 | 0 | 1 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `condition_fold` | `S0_ridge_true_sequence` | -0.0792768 | 0 | 5 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `condition_fold` | `S2_torch_mlp_true_sequence` | -0.0933424 | 0 | 5 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `temperature_holdout_fold` | `S0_ridge_true_sequence` | -0.130481 | 0 | 2 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `temperature_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.0965796 | 0 | 2 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `S0_ridge_true_sequence` | -0.159085 | 0 | 3 |
| `true_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `S2_torch_mlp_true_sequence` | -0.0971707 | 0 | 3 |
