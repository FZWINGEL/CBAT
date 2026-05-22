# Stress Feature Diagnostics

Source report: `reports/baselines/capacity_stress_features_hgb50_report.json`
F4 baseline report: `reports/baselines/capacity_hgb50_focused_report.json`
L0 reference report: `reports/baselines/capacity_l0_l3_report.json`
Generated at UTC: `2026-05-22T16:19:00.334191+00:00`

## Success Criteria

| Target | Split | Stress feature group | Stress MAE | F4 MAE | Gain vs F4 | Success |
|---|---|---|---:|---:|---:|---|
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `F6_coupled_stress` | 0.124656 | 0.125186 | 0.000530031 | True |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `F5_log_age_histograms` | 0.11026 | 0.101133 | -0.0091275 | False |

## Claim Readiness

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| Stress features improve C-rate holdout | not_supported | C-rate gains vs F4: 0.000530031, -0.0091275; condition rows: 24 | Do not claim stress-feature improvement |
| Stress features do not degrade condition/temperature folds | supported | condition degradation rows: 0; temperature degradation rows: 0 | Keep focused stress-feature ladder |
| Stress features authorize new modalities | blocked | Milestone 0.6 remains capacity-only and scalar-interval only. | Keep EIS/PULSE/CBAT blocked. |

## Outputs

- `plots/stress_feature_gain_by_split.csv`
- `plots/c_rate_stress_feature_errors.csv`
- `plots/stress_feature_claim_readiness.csv`
- C-rate condition rows: `24`
