# Milestone 2.6.2 Threshold-Warning Censoring Finalization

Date: 2026-05-23

## Scope

Milestone 2.6.2 tests whether the `capacity_below_80pct_initial`
threshold-warning result survives verified-only evaluation. This remains a
non-neural, leakage-safe threshold-event forecasting diagnostic. It is not
detector-knee prediction, calibrated risk, causal early warning, policy
ranking, or CBAT.

## Commands

```bash
mbp baseline run-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions-out data/processed/threshold_warning_l0_l2_predictions.parquet \
  --hgb-max-iter 50 \
  --label-policy all_rows

mbp baseline diagnose-threshold-warning \
  --report reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions data/processed/threshold_warning_l0_l2_predictions.parquet \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out-dir reports/baselines/threshold_warning_l0_l2

mbp baseline run-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_verified_only_report.json \
  --predictions-out data/processed/threshold_warning_verified_only_predictions.parquet \
  --hgb-max-iter 50 \
  --label-policy verified_only

mbp baseline compare-threshold-warning-censoring \
  --all-rows-report reports/baselines/threshold_warning_l0_l2_report.json \
  --verified-only-report reports/baselines/threshold_warning_verified_only_report.json \
  --out-dir reports/baselines/threshold_warning_censoring_sensitivity

mbp baseline finalize-threshold-warning-claim \
  --report reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions data/processed/threshold_warning_l0_l2_predictions.parquet \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --censoring-sensitivity reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md \
  --out-dir reports/baselines/threshold_warning_l0_l2
```

## Artifacts

- `reports/baselines/threshold_warning_verified_only_report.json`
- `reports/baselines/threshold_warning_verified_only/leaderboard.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`
- `reports/baselines/threshold_warning_censoring_sensitivity/threshold_warning_censoring_sensitivity_report.json`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_metric_comparison.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_split_comparison.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_c_rate_comparison.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_final_claim_readiness.md`
- `reports/baselines/threshold_warning_l0_l2/plots/final_lead_time_claim_matrix.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/final_c_rate_warning_matrix.csv`

Generated prediction Parquets remain ignored:

- `data/processed/threshold_warning_l0_l2_predictions.parquet`
- `data/processed/threshold_warning_verified_only_predictions.parquet`

## Censoring Result

For `event_within_3_checkups`, the all-row policy includes 3,827 rows:
494 positives and 3,333 negatives. The verified-only policy excludes 1,394
right-censored unknown rows and retains 2,433 rows: 494 positives and 1,939
observed negatives.

| Label policy | HGB W2 Brier | Event-rate prior Brier | Logistic proximity Brier | HGB gain vs prior | HGB gain vs proximity |
|---|---:|---:|---:|---:|---:|
| `all_rows` | `0.0655751` | `0.145791` | `0.132711` | `0.080216` | `0.067136` |
| `verified_only` | `0.090116` | `0.178655` | `0.168492` | `0.0885393` | `0.0783761` |

The threshold-warning signal survives verified-only evaluation.

## C-Rate Result

For the C-rate `event_within_3_checkups` row, verified-only evaluation retains
148 rows with 80 positives and 68 negatives.

| Model | Verified-only Brier | AUROC | AUPRC | ECE |
|---|---:|---:|---:|---:|
| `B0_event_rate_prior` | `0.377495` | `0.500000` | `0.778786` | `0.359359` |
| `B3_logistic_distance_baseline` | `0.327879` | `0.586949` | `0.660680` | `0.289104` |
| `B6_hist_gradient_boosting_classifier` W2 | `0.153370` | `0.966544` | `0.971457` | `0.194633` |

C-rate threshold-event forecasting is supported for diagnostics, but
calibration is not.

## Lead-Time Interpretation

The final claim remains threshold-event forecasting, not broad early warning.
Lead-time bins are reported in:

- `reports/baselines/threshold_warning_l0_l2/plots/final_lead_time_claim_matrix.csv`

Because near-threshold and censored regimes require separate interpretation,
early-warning wording remains exploratory.

## Decision

Authorized wording:

> Non-neural baselines can forecast the 80% capacity-relative threshold event
> diagnostically under grouped validation, beyond simple proximity baselines
> and under verified-only censoring sensitivity.

Blocked wording:

- calibrated risk;
- detector-knee prediction;
- causal early-warning claims;
- policy ranking;
- same-cell counterfactual claims;
- neural or sequence models;
- CBAT validation.

## Validation

Validation commands:

```bash
ruff check . --no-cache
pytest -p no:cacheprovider
git diff --check
```

Results:

- `ruff check . --no-cache`: passed.
- `pytest -p no:cacheprovider`: 141 passed.
- `git diff --check`: passed.
