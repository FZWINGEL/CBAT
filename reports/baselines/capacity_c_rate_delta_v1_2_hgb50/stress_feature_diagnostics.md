# Stress Feature Diagnostics

Source report: `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
F4 baseline report: `reports/baselines/capacity_hgb50_focused_report.json`
L0 reference report: `reports/baselines/capacity_l0_l3_report.json`
Generated at UTC: `2026-05-22T22:52:14.552713+00:00`

## Success Criteria

| Target | Split | Stress feature group | Stress MAE | F4 MAE | Gain vs F4 | Success |
|---|---|---|---:|---:|---:|---|
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `F8_timestamp_weighted_stress` | 0.102516 | 0.101133 | -0.00138302 | False |

## Claim Readiness

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| Stress features improve C-rate holdout | not_supported | C-rate gains vs F4: -0.00138302; condition rows: 12 | Do not claim stress-feature improvement |
| Stress features do not degrade condition/temperature folds | supported | condition degradation rows: 0; temperature degradation rows: 0 | Keep focused stress-feature ladder |
| Stress features authorize new modalities | blocked | Milestone 0.6 remains capacity-only and scalar-interval only. | Keep EIS/PULSE/CBAT blocked. |

## Outputs

- `plots/stress_feature_gain_by_split.csv`
- `plots/c_rate_stress_feature_errors.csv`
- `plots/stress_feature_claim_readiness.csv`
- C-rate condition rows: `12`
