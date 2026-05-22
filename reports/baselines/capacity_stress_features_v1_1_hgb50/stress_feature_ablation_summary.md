# Stress Feature Ablation Summary

This table compares F5-F10 against F4 within the existing v1.1 report.
No new model training is performed.

| Target | Model | Feature group | Gain vs F4 | Success |
|---|---|---|---:|---|
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.0291058 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F9_event_segmented_stress` | 0.0241516 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0234941 | True |
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0231586 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.0222064 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F6_coupled_stress` | 0.0190733 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F7_c_rate_focused` | 0.00501052 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.00458108 | True |
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F6_coupled_stress` | 0.00398415 | True |
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F9_event_segmented_stress` | 0.00285922 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.00274426 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.00128746 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F10_c_rate_v1_1` | -0.00107666 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | -0.00138302 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | -0.00140851 | False |
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F7_c_rate_focused` | -0.0042444 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | -0.00745853 | False |
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F10_c_rate_v1_1` | -0.00790515 | False |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F9_event_segmented_stress` | -0.0154236 | False |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F10_c_rate_v1_1` | -0.0160479 | False |

## Outputs

- `plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`
- `plots/c_rate_gain_by_feature_group.csv`
