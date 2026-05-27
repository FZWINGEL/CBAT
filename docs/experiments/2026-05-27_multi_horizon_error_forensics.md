# Milestone 6.1 - Multi-Horizon Error Forensics and Prospective Feature Audit

## Scope

Milestone 6.1 diagnoses the partial Milestone 6.0 multi-horizon capacity
forecasting result using existing artifacts only. It does not train a new
model, add feature engineering, or introduce a new scientific claim.

Inputs:

- `reports/baselines/capacity_horizon_l0_l2_report.json`
- `data/processed/capacity_horizon_l0_l2_predictions.parquet`
- `data/interim/capacity_horizon_table_v1.parquet`

Command:

```bash
mbp baseline diagnose-capacity-horizon \
  --report reports/baselines/capacity_horizon_l0_l2_report.json \
  --predictions data/processed/capacity_horizon_l0_l2_predictions.parquet \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --out-dir reports/baselines/capacity_horizon_l0_l2
```

## Outputs

- `reports/baselines/capacity_horizon_l0_l2/capacity_horizon_forensics_report.json`
- `reports/baselines/capacity_horizon_l0_l2/multi_horizon_error_forensics.md`
- `reports/baselines/capacity_horizon_l0_l2/multi_horizon_next_branch_readiness.md`
- `reports/baselines/capacity_horizon_l0_l2/plots/horizon_reference_gain_by_split.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/c_rate_condition_horizon_errors.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/prior_slope_failure_modes.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/oracle_exposure_gain_by_split.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/prospective_feature_audit.csv`

## Findings

The global Milestone 6.0 decision remains unchanged. Prospective HGB K2 is
strong for C-rate horizons 2 and 3, and for all-split delta-capacity horizons
2 and 3, but all-split horizon-3 capacity level remains a near miss against
the prior-slope baseline.

| Split | Target | Horizon | HGB K2 MAE | Prior-slope MAE | Gain vs prior | Beats both |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| all | `capacity_Ah_kh` | 2 | 0.0773609 | 0.0793428 | 0.00198181 | true |
| all | `capacity_Ah_kh` | 3 | 0.0935304 | 0.0932329 | -0.000297496 | false |
| all | `delta_capacity_Ah_h` | 2 | 0.0722043 | 0.0793428 | 0.00713843 | true |
| all | `delta_capacity_Ah_h` | 3 | 0.0807277 | 0.0932329 | 0.0125052 | true |
| C-rate | `capacity_Ah_kh` | 2 | 0.183684 | 0.299260 | 0.115576 | true |
| C-rate | `capacity_Ah_kh` | 3 | 0.221461 | 0.302605 | 0.0811434 | true |
| C-rate | `delta_capacity_Ah_h` | 2 | 0.183020 | 0.299260 | 0.116240 | true |
| C-rate | `delta_capacity_Ah_h` | 3 | 0.232468 | 0.302605 | 0.0701366 | true |

The diagnostic run produced 48 split/reference gain rows, 720 C-rate
condition-level error rows, 1,184 prior-slope failure-mode rows, and 48
oracle-exposure gain rows. K3 oracle exposure improves over K2 in 43 rows, but
those gains remain non-prospective because K3 uses realized k-to-k+h exposure.

The prior-slope failure-mode table shows the largest HGB-versus-prior-slope
regressions in late-life and low-SOH bins, especially for horizon 5 and some
profile/voltage-window views. This suggests that any future technical branch
should focus on prior-trajectory shape available at check-up `k`, not on
future exposure, sequence models, or architecture.

## Decision

Claim posture:

- global multi-horizon forecasting remains `partially_supported`;
- C-rate multi-horizon forecasting remains `supported_for_diagnostics`;
- K3 oracle exposure remains `oracle_diagnostic_only`;
- calibrated risk, calibrated uncertainty, policy ranking, sequence/neural
  models, causal claims, and CBAT remain blocked.

Recommended future branch, if technical work continues:

> `prior_trajectory_shape_audit`

This would need to be predeclared and prospective: only capacity trajectory
shape, slope, curvature, or stability features observed at or before check-up
`k` may be used.
