# Capacity Target Consistency Diagnostics

Source report: `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
Generated at UTC: `2026-05-22T22:35:21.626416+00:00`

This diagnostic checks whether the algebraic relationship
`capacity_Ah_k1 = capacity_Ah_k + delta_capacity_Ah` changes the
interpretation of direct target-specific predictions.

## C-Rate Direct Vs Derived

| Target | Model | Feature group | Direct MAE | Derived MAE | Derived - direct | Derived better |
|---|---|---|---:|---:|---:|---|
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.0881449 | 0.0762576 | -0.0118873 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.0882133 | 0.0767371 | -0.0114762 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0876827 | 0.0808812 | -0.00680147 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0918404 | 0.0817342 | -0.0101062 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F9_event_segmented_stress` | 0.0975281 | 0.0986922 | 0.00116409 | False |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.118638 | 0.102218 | -0.0164195 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F10_c_rate_v1_1` | 0.107542 | 0.121077 | 0.0135354 | False |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F5_log_age_histograms` | 0.115303 | 0.108244 | -0.00705882 | True |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F7_c_rate_focused` | 0.111581 | 0.118161 | 0.00658029 | False |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F6_coupled_stress` | 0.118544 | 0.117729 | -0.000814395 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F9_event_segmented_stress` | 0.118587 | 0.120243 | 0.00165655 | False |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.1347 | 0.124326 | -0.0103745 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F7_c_rate_focused` | 0.141185 | 0.132471 | -0.00871449 | True |
| `capacity_Ah_k1` | `L3_quantile_hist_gradient_boosting` | `F10_c_rate_v1_1` | 0.141802 | 0.133579 | -0.00822216 | True |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.0762576 | 0.0881449 | 0.0118873 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.0767371 | 0.0882133 | 0.0114762 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0808812 | 0.0876827 | 0.00680147 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0817342 | 0.0918404 | 0.0101062 | False |
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F9_event_segmented_stress` | 0.0986922 | 0.0975281 | -0.00116409 | True |
| `delta_capacity_Ah` | `L3_quantile_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.102218 | 0.118638 | 0.0164195 | False |

## Decision Signal

C-rate delta rows where derived delta beats direct delta: `4/14`.

If derived delta consistently beats direct delta on C-rate, report a
capacity-first target path before adding new stress features. If direct
delta remains stronger, the failure is not only target formulation.

## Outputs

- `plots/derived_delta_from_capacity_metrics.csv`
- `plots/derived_capacity_from_delta_metrics.csv`
- `plots/direct_vs_derived_target_metrics.csv`
- Target metric rows: `1232`
