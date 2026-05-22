# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_stress_features_hgb50_report.json`
Generated at UTC: `2026-05-22T16:18:55.030969+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`
L0 reference report: `reports/baselines/capacity_l0_l3_report.json`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0416927 | `reference_report` | 0.096318 | 67 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0446189 | `reference_report` | 0.105637 | 67 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.0502775 | `reference_report` | 0.0877332 | 36 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.063644 | `reference_report` | 0.0866123 | 23 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0708447 | `reference_report` | 0.0478819 | 36 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0844129 | `reference_report` | 0.0343138 | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 | 20 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.124656 | `reference_report` | 0.210198 | 32 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.124656 | `reference_report` | 0.210198 |

## Feature Gains

Primary feature-gain rows: `64`
Mean primary adjacent-feature gain: `-0.00158135`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `220`
Mean primary-minus-sensitivity condition-mean MAE: `-0.00419579`
Median primary-minus-sensitivity condition-mean MAE: `-0.00345194`

## Diagnostic Tables

- `plots/best_by_target_split.csv`
- `plots/feature_gain_by_split.csv`
- `plots/c_rate_holdout_errors.csv`
- `plots/c_rate_holdout_by_condition.csv`
- `plots/c_rate_grouped_summaries.csv`
- `plots/strict_vs_tolerant_delta.csv`
- `plots/worst_condition_errors.csv`
- `c_rate_holdout_error_analysis.md`
- `claim_readiness.md`

C-rate diagnostic rows: `24`
C-rate grouped summary rows: `31`
