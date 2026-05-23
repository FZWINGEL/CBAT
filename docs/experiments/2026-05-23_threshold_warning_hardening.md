# Milestone 2.6.1 Threshold-Warning Hardening

Date: 2026-05-23

## Scope

Milestone 2.6.1 hardens the `capacity_below_80pct_initial` threshold-event
warning result. This is a prospective non-neural threshold-event forecasting
check, not detector-knee prediction, calibrated risk, policy ranking, or a
causal warning claim.

Allowed inputs remain check-up-`k` state/time/nominal fields. Future capacity,
capacity deltas, future interval exposure, future PULSE/EIS state, and
PULSE/EIS deltas remain excluded from warning features.

## Commands

```bash
mbp baseline run-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions-out data/processed/threshold_warning_l0_l2_predictions.parquet \
  --hgb-max-iter 50

mbp baseline diagnose-threshold-warning \
  --report reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions data/processed/threshold_warning_l0_l2_predictions.parquet \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out-dir reports/baselines/threshold_warning_l0_l2
```

## Artifacts

- `reports/baselines/threshold_warning_l0_l2_report.json`
- `reports/baselines/threshold_warning_l0_l2/leaderboard.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_claim_readiness.md`
- `reports/baselines/threshold_warning_l0_l2/lead_time_diagnostics.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_censoring_report.json`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_censoring_by_split.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_reliability.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration_by_split.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration_by_c_rate.md`
- `reports/baselines/threshold_warning_l0_l2/plots/lead_time_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/proximity_bin_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/c_rate_lead_time_performance.csv`

Generated prediction Parquet remains ignored:

- `data/processed/threshold_warning_l0_l2_predictions.parquet`

## Results

The hardening run generated 468 grouped metric rows. The 3-check-up horizon
remains the most useful primary diagnostic horizon.

For `event_within_3_checkups`, HGB W2 improves mean Brier beyond both the
event-rate prior and the best distance/proximity baseline:

| Model | Feature group | Mean Brier | Mean AUROC | Mean AUPRC |
|---|---|---:|---:|---:|
| `B0_event_rate_prior` | `prior_rate` | `0.145791` | `0.500000` | `0.181899` |
| `B3_logistic_distance_baseline` | `distance_to_threshold` | `0.132711` | `0.654404` | `0.307341` |
| `B6_hist_gradient_boosting_classifier` | `W2_nominal` | `0.0655751` | `0.939121` | `0.791905` |

The C-rate 3-check-up row also stays positive after proximity hardening:

| Model | Brier | AUROC | AUPRC | Positives / negatives |
|---|---:|---:|---:|---:|
| `B0_event_rate_prior` | `0.407317` | `0.500000` | `0.717359` | `80 / 77` |
| `B3_logistic_distance_baseline` | `0.355265` | `0.523539` | `0.519035` | `80 / 77` |
| `B6_hist_gradient_boosting_classifier` W2 | `0.159930` | `0.940341` | `0.946054` | `80 / 77` |

## Lead Time

Lead-time and proximity-bin diagnostics are reported in:

- `reports/baselines/threshold_warning_l0_l2/lead_time_diagnostics.md`
- `reports/baselines/threshold_warning_l0_l2/plots/lead_time_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/proximity_bin_performance.csv`

These diagnostics separate near-threshold behavior from longer-lead rows. They
support interpretation as threshold-event forecasting, but do not yet authorize
a broad early-warning claim.

## Censoring

The censoring audit records:

| Target | Positive observed | Negative observed | Right-censored unknown |
|---|---:|---:|---:|
| `event_within_1_checkup` | `173` | `2260` | `1394` |
| `event_within_2_checkups` | `346` | `2087` | `1394` |
| `event_within_3_checkups` | `494` | `1939` | `1394` |

The current Boolean horizon labels implicitly treat right-censored unknown rows
as negative. Verified-only sensitivity is therefore required before any
stronger early-warning wording.

## Calibration

Calibration remains not supported. For the C-rate `event_within_3_checkups`
HGB W2 row, ECE is `0.174673`. Probability outputs should be interpreted as
diagnostic scores, not calibrated event-risk estimates.

## Decision

Milestone 2.6.1 supports a narrow diagnostic claim:

> Non-neural baselines can forecast `capacity_below_80pct_initial` threshold
> events under grouped validation, beyond simple proximity baselines.

The following remain blocked:

- calibrated risk;
- detector-knee prediction;
- causal early-warning claims;
- policy ranking;
- neural or sequence models;
- CBAT.

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
