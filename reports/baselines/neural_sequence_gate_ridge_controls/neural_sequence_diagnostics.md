# Neural Sequence Gate Diagnostics

Positive gain means the neural sequence candidate has lower condition-mean MAE.

| Comparison | Target | Split | Model | Mean gain | P05 gain | Positive rows | Rows |
|---|---|---|---|---:|---:|---:|---:|
| `true_neural_sequence_vs_shuffled` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `NS1_ridge_flat_true_sequence` | 0.0158411 | 0.0158411 | 1 | 1 |
| `true_neural_sequence_vs_shuffled` | `capacity_Ah_k1` | `condition_fold` | `NS1_ridge_flat_true_sequence` | 0.0130765 | -0.00560168 | 4 | 5 |
| `true_neural_sequence_vs_shuffled` | `capacity_Ah_k1` | `profile_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.16829 | -0.16829 | 0 | 1 |
| `true_neural_sequence_vs_shuffled` | `capacity_Ah_k1` | `temperature_holdout_fold` | `NS1_ridge_flat_true_sequence` | 0.335366 | 0.0659191 | 2 | 2 |
| `true_neural_sequence_vs_shuffled` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.0351523 | -0.0703133 | 1 | 3 |
| `true_neural_sequence_vs_shuffled` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.0267019 | -0.0267019 | 0 | 1 |
| `true_neural_sequence_vs_shuffled` | `delta_capacity_Ah` | `condition_fold` | `NS1_ridge_flat_true_sequence` | 0.00357214 | -0.0128821 | 2 | 5 |
| `true_neural_sequence_vs_shuffled` | `delta_capacity_Ah` | `profile_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.145022 | -0.145022 | 0 | 1 |
| `true_neural_sequence_vs_shuffled` | `delta_capacity_Ah` | `temperature_holdout_fold` | `NS1_ridge_flat_true_sequence` | 0.312732 | 0.0858074 | 2 | 2 |
| `true_neural_sequence_vs_shuffled` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.0465267 | -0.0612092 | 0 | 3 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.440671 | -0.440671 | 0 | 1 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `condition_fold` | `NS1_ridge_flat_true_sequence` | -0.096602 | -0.114689 | 0 | 5 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `profile_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.218297 | -0.218297 | 0 | 1 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `temperature_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.192622 | -0.301154 | 0 | 2 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.192936 | -0.269147 | 0 | 3 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.503859 | -0.503859 | 0 | 1 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `condition_fold` | `NS1_ridge_flat_true_sequence` | -0.106766 | -0.125955 | 0 | 5 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `profile_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.198476 | -0.198476 | 0 | 1 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `temperature_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.164219 | -0.257053 | 0 | 2 |
| `true_neural_sequence_vs_event_aggregate_hgb` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.168426 | -0.238623 | 0 | 3 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `c_rate_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.449802 | -0.449802 | 0 | 1 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `condition_fold` | `NS1_ridge_flat_true_sequence` | -0.097785 | -0.116717 | 0 | 5 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `temperature_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.199397 | -0.309222 | 0 | 2 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `capacity_Ah_k1` | `voltage_window_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.117012 | -0.122615 | 0 | 3 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `c_rate_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.496807 | -0.496807 | 0 | 1 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `condition_fold` | `NS1_ridge_flat_true_sequence` | -0.109269 | -0.130935 | 0 | 5 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `temperature_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.168416 | -0.263169 | 0 | 2 |
| `true_neural_sequence_vs_timestamp_stress_hgb` | `delta_capacity_Ah` | `voltage_window_holdout_fold` | `NS1_ridge_flat_true_sequence` | -0.117619 | -0.147239 | 0 | 3 |
