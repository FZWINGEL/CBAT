# Milestone 6.0 - Multi-Horizon Capacity Forecasting Gate

## Scope

Milestone 6.0 tests a charter-aligned Q1 extension: whether non-neural models
can forecast capacity over multiple future check-up horizons under grouped
condition and stressor holdouts.

This is not an architecture, sequence, policy, or causal milestone. It uses
only existing interval-table evidence. K0-K2 feature groups are prospective;
K3 aggregates the actual k-to-k+h interval exposure and is oracle-diagnostic
only.

## Commands

```bash
mbp analysis build-capacity-horizon-table \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/capacity_horizon_table_v1.parquet \
  --horizons 1,2,3,5

mbp analysis capacity-horizon-qa \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/analysis/capacity_horizon/capacity_horizon_qa_report.json \
  --coverage-out reports/analysis/capacity_horizon/capacity_horizon_coverage.csv

mbp baseline run-capacity-horizon \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --out reports/baselines/capacity_horizon_l0_l2_report.json \
  --predictions-out data/processed/capacity_horizon_l0_l2_predictions.parquet \
  --out-dir reports/baselines/capacity_horizon_l0_l2 \
  --targets capacity_Ah_kh,delta_capacity_Ah_h \
  --horizons 1,2,3,5 \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --model-levels MH0_persistence,MH1_prior_slope_linear,MH2_ridge,MH3_hist_gradient_boosting \
  --feature-groups K0_prior_capacity,K1_prior_state_time,K2_nominal_condition,K3_oracle_exposure_diagnostic \
  --hgb-max-iter 50
```

## Data Product QA

`capacity_horizon_table_v1.parquet` contains 13,770 rows across 228 cells and
76 parameter sets:

| Horizon | Rows | Cells | Parameter sets | C-rate rows |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3,827 | 228 | 76 | 157 |
| 2 | 3,599 | 226 | 76 | 121 |
| 3 | 3,373 | 204 | 68 | 87 |
| 5 | 2,971 | 189 | 64 | 50 |

QA passed with no missing/censored rows among observed possible starts for the
selected horizons.

## Baselines

Models:

- `MH0_persistence`
- `MH1_prior_slope_linear`
- `MH2_ridge`
- `MH3_hist_gradient_boosting`

Feature groups:

- `K0_prior_capacity`
- `K1_prior_state_time`
- `K2_nominal_condition`
- `K3_oracle_exposure_diagnostic`

K3 uses actual horizon exposure and is not a prospective input.

## Main Results

Across all grouped split rows, HGB K2 beats both persistence and prior-slope
baselines for horizon-2 capacity level and horizons 2/3 delta capacity. The
horizon-3 capacity-level row is a near tie but narrowly worse than prior slope.

| Target | Horizon | Persistence MAE | Prior-slope MAE | HGB K2 MAE | K3 oracle MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| `capacity_Ah_kh` | 2 | 0.135459 | 0.0793428 | 0.0773609 | 0.0696759 |
| `capacity_Ah_kh` | 3 | 0.166195 | 0.0932329 | 0.0935304 | 0.0774983 |
| `delta_capacity_Ah_h` | 2 | 0.135459 | 0.0793428 | 0.0722043 | 0.0639527 |
| `delta_capacity_Ah_h` | 3 | 0.166195 | 0.0932329 | 0.0807277 | 0.0692963 |

C-rate horizons 2 and 3 are stronger:

| Target | Horizon | Persistence MAE | Prior-slope MAE | HGB K2 MAE |
| --- | ---: | ---: | ---: | ---: |
| `capacity_Ah_kh` | 2 | 0.433943 | 0.299260 | 0.183684 |
| `capacity_Ah_kh` | 3 | 0.492851 | 0.302605 | 0.221461 |
| `delta_capacity_Ah_h` | 2 | 0.433943 | 0.299260 | 0.183020 |
| `delta_capacity_Ah_h` | 3 | 0.492851 | 0.302605 | 0.232468 |

The oracle diagnostic group improves several rows, which suggests actual
horizon exposure contains signal, but that cannot be used as prospective
forecasting evidence.

## Claim Decision

Supported for diagnostics:

- C-rate multi-horizon forecasting with prospective K2 HGB for horizons 2 and
  3.
- Delta-capacity multi-horizon forecasting for horizons 2 and 3.

Partially supported:

- Overall multi-horizon capacity forecasting, because horizon-3
  `capacity_Ah_kh` narrowly misses the prior-slope baseline.

Diagnostic only:

- K3 oracle exposure gains.

Blocked:

- calibrated uncertainty;
- calibrated risk;
- policy ranking;
- sequence/neural models;
- CBAT;
- causal or same-cell counterfactual claims;
- claims that C-rate fade is solved globally.
