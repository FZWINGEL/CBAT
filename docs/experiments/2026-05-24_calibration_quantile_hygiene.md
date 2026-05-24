# Calibration Metric Sensitivity and Quantile Noncrossing Hygiene

Date: 2026-05-24

Milestone 5.2 performs two scoped hygiene changes requested during review:

- add equal-frequency ECE alongside the existing fixed-width ECE for
  threshold-warning calibration sensitivity;
- enforce noncrossing q10/q50/q90 endpoints for independently fitted L3
  capacity quantile HGB models by row-wise sorting evaluated endpoints while
  preserving the q50 point prediction.

This milestone does not add new feature engineering, new model families,
neural or sequence models, policy ranking, CBAT, calibrated-risk wording, or
calibrated-uncertainty wording.

## Review Decisions

The LOG_AGE global-sort proposal was not implemented. LOG_AGE ingestion already
writes row groups from single-cell CSV chunks, so a global sort would risk
memory blow-up without clear scan-time benefit.

The threshold-warning LOCF imputation proposal was not implemented. It would be
feature-engineering and encoder-shape work, while current warning rows are
constructed from observed check-up states. A NaN audit should precede any such
change.

## Commands

Threshold-warning reports were refreshed with the additive ECE metric:

```bash
.venv/bin/mbp baseline run-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions-out data/processed/threshold_warning_l0_l2_predictions.parquet

.venv/bin/mbp baseline run-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --label-policy verified_only \
  --out reports/baselines/threshold_warning_verified_only_report.json \
  --predictions-out data/processed/threshold_warning_verified_only_predictions.parquet

.venv/bin/mbp baseline compare-threshold-warning-censoring \
  --all-rows-report reports/baselines/threshold_warning_l0_l2_report.json \
  --verified-only-report reports/baselines/threshold_warning_verified_only_report.json \
  --out-dir reports/baselines/threshold_warning_censoring_sensitivity

.venv/bin/mbp baseline finalize-threshold-warning-claim \
  --report reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions data/processed/threshold_warning_l0_l2_predictions.parquet \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --censoring-sensitivity reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md \
  --out-dir reports/baselines/threshold_warning_l0_l2
```

Probability calibration was refreshed:

```bash
.venv/bin/mbp baseline calibrate-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_calibration_report.json \
  --predictions-out data/processed/threshold_warning_calibrated_predictions.parquet \
  --out-dir reports/baselines/threshold_warning_calibration \
  --targets event_within_1_checkup,event_within_2_checkups,event_within_3_checkups \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --label-policies all_rows,verified_only \
  --hgb-max-iter 50
```

Capacity quantile reports were refreshed after noncrossing endpoint hygiene:

```bash
.venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --out reports/baselines/capacity_hgb50_focused_report.json \
  --predictions-out data/processed/capacity_hgb50_focused_predictions.parquet \
  --model-levels L2_hist_gradient_boosting,L3_quantile_hist_gradient_boosting \
  --feature-groups F1_state_time,F2_state_exposure,F3_state_nominal,F4_state_log_age_scalar \
  --hgb-max-iter 50

.venv/bin/mbp analysis calibrate-capacity \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --interval-table data/interim/interval_table.parquet \
  --replicate-spread reports/analysis/replicate_uncertainty/replicate_spread_by_condition.csv \
  --out-dir reports/analysis/calibration_capacity
```

Generated prediction Parquets remain local ignored artifacts and should not be
committed.

## Threshold-Warning Calibration Result

Equal-frequency ECE mostly agrees with the fixed-width decision posture. For
the primary `event_within_3_checkups` horizon:

| Method | Label policy | Raw fixed ECE | Method fixed ECE | Raw equal-freq ECE | Method equal-freq ECE |
|---|---|---:|---:|---:|---:|
| Platt | all rows | 0.065169 | 0.0607504 | 0.0627156 | 0.0616616 |
| Platt | verified only | 0.0973711 | 0.0749807 | 0.090753 | 0.072939 |
| Isotonic | all rows | 0.065169 | 0.0562111 | 0.0627156 | 0.0565418 |
| Isotonic | verified only | 0.0973711 | 0.0725802 | 0.090753 | 0.0706746 |

The C-rate guardrail still fails:

| Method | Label policy | Fixed-width ECE | Equal-frequency ECE | Brier |
|---|---|---:|---:|---:|
| Raw HGB W2 | verified only | 0.214827 | 0.21526 | 0.190892 |
| Platt | verified only | 0.167813 | 0.176461 | 0.148773 |
| Isotonic | verified only | 0.159021 | 0.159021 | 0.147795 |

Decision: equal-frequency ECE is useful sensitivity reporting, but it does not
authorize calibrated-risk wording.

## Capacity Quantile Result

Noncrossing q10/q50/q90 endpoint sorting is now applied after independent L3
quantile prediction. The q50 point prediction remains the independent median
model output.

The refreshed reports still block calibrated-capacity uncertainty:

- capacity claim-readiness mean q10-q90 coverage: `0.696702`;
- calibration report raw q10-q90 mean coverage: `0.701398`;
- calibration report raw q10-q90 min coverage: `0.00226244`;
- all-method C-rate mean coverage: `0.72293`.

Decision: quantile noncrossing is report hygiene only. Raw quantile intervals
remain diagnostic and undercovered.

## Claim Posture

Allowed wording:

> Calibration diagnostics now report both fixed-width and equal-frequency ECE,
> and L3 capacity quantile intervals are noncrossing after post-sort hygiene.

Forbidden wording:

> Threshold-warning probabilities are calibrated risk estimates.

> HGB quantile intervals are calibrated uncertainty.

> Stressor-robust training solves C-rate fade or authorizes architecture work.

Calibrated risk, calibrated capacity uncertainty, detector-knee prediction,
policy ranking, causal claims, sequence/neural models, DRT, EIS embeddings, and
CBAT remain blocked.
