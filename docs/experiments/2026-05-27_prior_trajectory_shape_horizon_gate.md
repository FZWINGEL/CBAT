# Milestone 6.2 - Prior-Trajectory Shape Horizon Gate

## Scope

Milestone 6.2 tests whether capacity trajectory shape observed at or before
check-up `k` improves the non-neural multi-horizon capacity forecast from
Milestone 6.0. This is the only follow-up branch authorized by the Milestone
6.1 forensics report.

This milestone does not use future k-to-k+h exposure as a prospective input,
does not train neural or sequence models, and does not authorize policy,
causal, calibrated-risk, calibrated-uncertainty, or CBAT claims.

## Commands

```bash
mbp analysis build-capacity-horizon-trajectory-features \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/capacity_horizon_trajectory_features_v1.parquet

mbp analysis capacity-horizon-trajectory-qa \
  --trajectory-features data/interim/capacity_horizon_trajectory_features_v1.parquet \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --out reports/analysis/capacity_horizon/capacity_horizon_trajectory_qa_report.json \
  --coverage-out reports/analysis/capacity_horizon/capacity_horizon_trajectory_coverage.csv

mbp baseline run-capacity-horizon \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --trajectory-features data/interim/capacity_horizon_trajectory_features_v1.parquet \
  --out reports/baselines/capacity_horizon_trajectory_l0_l2_report.json \
  --predictions-out data/processed/capacity_horizon_trajectory_l0_l2_predictions.parquet \
  --out-dir reports/baselines/capacity_horizon_trajectory_l0_l2 \
  --targets capacity_Ah_kh,delta_capacity_Ah_h \
  --horizons 1,2,3,5 \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --model-levels MH0_persistence,MH1_prior_slope_linear,MH2_ridge,MH3_hist_gradient_boosting \
  --feature-groups K0_prior_capacity,K1_prior_state_time,K2_nominal_condition,K4_prior_trajectory_shape,K5_nominal_plus_trajectory_shape \
  --hgb-max-iter 50

mbp baseline diagnose-capacity-horizon-trajectory \
  --report reports/baselines/capacity_horizon_trajectory_l0_l2_report.json \
  --predictions data/processed/capacity_horizon_trajectory_l0_l2_predictions.parquet \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --out-dir reports/baselines/capacity_horizon_trajectory_l0_l2
```

## Data Product QA

`capacity_horizon_trajectory_features_v1.parquet` contains 13,770 rows keyed
to the capacity horizon table. QA passed:

- duplicate keys: 0;
- missing horizon keys: 0;
- extra trajectory keys: 0;
- leakage columns: 0.

Rows at check-up 0 have no prior history by construction. This is reported as
a warning, not a failure.

## Results

The trajectory feature groups are:

- `K4_prior_trajectory_shape`;
- `K5_nominal_plus_trajectory_shape`.

The central repair test fails. K5 does not repair the all-split horizon-3
capacity-level near miss:

| Feature group | Candidate MAE | K2 MAE | Prior-slope MAE | Gain vs K2 | Gain vs prior |
| --- | ---: | ---: | ---: | ---: | ---: |
| `K4_prior_trajectory_shape` | 0.103741 | 0.0935304 | 0.0932329 | -0.0102109 | -0.0105084 |
| `K5_nominal_plus_trajectory_shape` | 0.0981241 | 0.0935304 | 0.0932329 | -0.00459367 | -0.00489117 |

C-rate preservation is mixed. K5 improves C-rate horizon-2 `capacity_Ah_kh`
and horizon-3 `delta_capacity_Ah_h`, but it worsens C-rate horizon-3
`capacity_Ah_kh` and horizon-2 `delta_capacity_Ah_h` relative to K2.

| Target | Horizon | K5 MAE | K2 MAE | Gain vs K2 | Beats references |
| --- | ---: | ---: | ---: | ---: | --- |
| `capacity_Ah_kh` | 2 | 0.180306 | 0.183684 | 0.00337836 | true |
| `capacity_Ah_kh` | 3 | 0.225614 | 0.221461 | -0.00415229 | false |
| `delta_capacity_Ah_h` | 2 | 0.190892 | 0.183020 | -0.00787165 | false |
| `delta_capacity_Ah_h` | 3 | 0.226924 | 0.232468 | 0.00554458 | true |

## Decision

Prior-trajectory shape is `partially_supported` as a diagnostic feature family,
but it does not pass the predeclared repair gate:

- horizon-3 capacity repair: `not_supported`;
- C-rate horizon-2/3 preservation: `not_supported`;
- trajectory leakage audit: `passed`.

Do not claim that trajectory shape solves multi-horizon forecasting. Do not
open sequence/neural models, CBAT, policy ranking, causal claims, calibrated
risk, or calibrated uncertainty from this result.
