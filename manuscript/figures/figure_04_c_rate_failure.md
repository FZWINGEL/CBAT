# Figure 04: C-Rate Failure Analysis

Claim supported: C03 C-rate holdout is hardest.

Source artifacts:

- `reports/baselines/capacity_hgb50_focused/c_rate_holdout_error_analysis.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_temperature.csv`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_voltage_window.csv`

Intended plot type: heatmap or faceted bar chart by temperature and voltage
window.

Key numbers:

- C-rate `capacity_Ah_k1` F4 condition-mean MAE: `0.125186`.
- C-rate `delta_capacity_Ah` F4 condition-mean MAE: `0.101133`.
- Worst conditions include cold/cool high-C-rate parameter sets.

Risk/limitation:

- C-rate condition count is limited; avoid overfitting the narrative to a few
  parameter sets.

Caption draft:

> C-rate holdout error structure. The hardest capacity errors concentrate in
> cold/cool high-C-rate and wide-voltage-window conditions, motivating but not
> validating additional stress-feature or PULSE claims.
