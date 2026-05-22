# Capacity Baseline Diagnostics

Source report: `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
Generated at UTC: `2026-05-22T22:17:18.790046+00:00`
Schema version: `gate5.capacity_baseline.v1`
HGB max iterations: `50`
Numeric standardization: `train_fold_mean_std`
L0 reference report: `reports/baselines/capacity_l0_l3_report.json`

## Best Rows By Target And Split

| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |
|---|---|---|---|---:|---|---:|---:|
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` | `F8_timestamp_weighted_stress` | 0.0417003 | `reference_report` | 0.0963104 | 70 |
| `delta_capacity_Ah` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.0480717 | `reference_report` | 0.102185 | 67 |
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.0529301 | `reference_report` | 0.0850806 | 36 |
| `capacity_Ah_k1` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `F6_coupled_stress` | 0.0641161 | `reference_report` | 0.0861402 | 23 |
| `delta_capacity_Ah` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F10_c_rate_v1_1` | 0.0705301 | `reference_report` | 0.0481965 | 36 |
| `capacity_Ah_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.0844129 | `reference_report` | 0.0343138 | 36 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 | 20 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.120605 | `reference_report` | 0.214249 | 36 |

## C-Rate Holdout

The C-rate holdout remains the hardest split in the bounded capacity runs.

| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |
|---|---|---|---:|---|---:|
| `delta_capacity_Ah` | `L2_hist_gradient_boosting` | `F4_state_log_age_scalar` | 0.101133 | `reference_report` | 0.233721 |
| `capacity_Ah_k1` | `L2_hist_gradient_boosting` | `F5_log_age_histograms` | 0.120605 | `reference_report` | 0.214249 |

## Feature Gains

Primary feature-gain rows: `96`
Mean primary adjacent-feature gain: `-0.001232`

Positive gain means the later feature group reduced condition-mean MAE.

## Strict Vs Tolerant Sensitivity

Sensitivity rows: `308`
Mean primary-minus-sensitivity condition-mean MAE: `-0.00382811`
Median primary-minus-sensitivity condition-mean MAE: `-0.00318164`

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
