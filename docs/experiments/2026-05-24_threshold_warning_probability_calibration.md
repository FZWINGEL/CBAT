# Threshold-Warning Probability Calibration

Date: 2026-05-24

Milestone 5.0 evaluates whether the existing non-neural 80% threshold-event
warning diagnostic can support calibrated probability wording. This is a
post-hoc calibration gate only; it does not add new features, detector-knee
prediction, policy ranking, CBAT, neural models, sequence models, or causal
claims.

## Command

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

The generated prediction Parquet is a local ignored artifact and should not be
committed.

## Calibration Policy

For each grouped split instance, calibration conditions are reserved from the
non-test side. The base HGB W2 model is fit on the remaining fit conditions,
post-hoc calibrators are fit on calibration conditions, and metrics are
reported on held-out test conditions. The leakage audit uses only check-up-`k`
state/time/nominal features already accepted for the threshold-warning
baseline.

Methods:

- `C0_raw_hgb_w2`
- `C1_platt_logistic`
- `C2_isotonic`

Label policies:

- `all_rows`
- `verified_only`

## Result

For the primary `event_within_3_checkups` horizon, post-hoc calibration
improves mean grouped ECE:

| Method | Label policy | Mean ECE | Mean Brier | Mean log loss |
|---|---|---:|---:|---:|
| Raw HGB W2 | all rows | 0.065169 | 0.073546 | 0.281280 |
| Platt | all rows | 0.060750 | 0.071238 | 0.253596 |
| Isotonic | all rows | 0.056211 | 0.069726 | 0.409522 |
| Raw HGB W2 | verified only | 0.097371 | 0.099642 | 0.360602 |
| Platt | verified only | 0.074981 | 0.084607 | 0.280163 |
| Isotonic | verified only | 0.072580 | 0.083854 | 0.416529 |

The C-rate guardrail fails:

| Method | Label policy | C-rate ECE | C-rate Brier |
|---|---|---:|---:|
| Raw HGB W2 | all rows | 0.222194 | 0.198580 |
| Platt | all rows | 0.208924 | 0.174262 |
| Isotonic | all rows | 0.192354 | 0.163916 |
| Raw HGB W2 | verified only | 0.214827 | 0.190892 |
| Platt | verified only | 0.167813 | 0.148773 |
| Isotonic | verified only | 0.159021 | 0.147795 |

The strict calibration rule requires all-row and verified-only ECE gains,
no material Brier/log-loss degradation, C-rate ECE no greater than 0.10, and
no leakage. No method passes all guardrails.

## Decision

Post-hoc calibration is useful diagnostically: Platt improves mean ECE and
Brier without the isotonic log-loss penalty, and isotonic gives the lowest mean
ECE/Brier in several rows. But C-rate ECE remains too high, so calibrated-risk
wording is not authorized.

Allowed wording:

> Post-hoc calibration improves average threshold-warning probability
> diagnostics, but C-rate calibration remains insufficient; probabilities
> should be treated as diagnostic scores.

Forbidden wording:

> Threshold-warning probabilities are calibrated risk estimates.

Detector-knee prediction, policy ranking, causal warning claims, CBAT, neural
models, sequence models, DRT, EIS embeddings, and broad multimodal claims
remain blocked.
