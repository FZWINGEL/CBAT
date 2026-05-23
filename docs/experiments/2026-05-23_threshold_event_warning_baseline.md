# Milestone 2.6: Non-Neural Threshold-Event Early-Warning Baseline Gate

Date: 2026-05-23

## Scope

Milestone 2.6 evaluates whether the more stable threshold-event label
`capacity_below_80pct_initial` can support a narrow, non-neural prospective
warning baseline under grouped validation. This is not detector-knee
prediction. It does not authorize neural models, sequence models, transformers,
CBAT, policy ranking, causal/mechanistic claims, same-cell counterfactual
claims, or calibrated-risk claims.

## Leakage Policy

The warning table uses only information available at or before check-up `k`.
Allowed fields include prior capacity state, SOH at `k`, check-up index,
calendar day at `k`, cumulative EFC at `k`, and nominal condition metadata.

Forbidden fields are excluded:

- `capacity_Ah_k1`
- `delta_capacity_Ah`
- LOG_AGE exposure from `k -> k+1`
- stress sidecars summarizing `k -> k+1`
- PULSE/EIS at `k1`
- PULSE/EIS deltas
- threshold target fields as features

## Commands

```bash
mbp analysis build-threshold-warning-table \
  --threshold-labels data/interim/threshold_event_label_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/threshold_warning_table_v1.parquet \
  --threshold capacity_below_80pct_initial

mbp analysis threshold-warning-qa \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/analysis/knee/threshold_warning_qa_report.json \
  --class-balance-out reports/analysis/knee/threshold_warning_class_balance.csv \
  --split-coverage-out reports/analysis/knee/threshold_warning_split_coverage.csv

mbp baseline run-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_l0_l2_report.json \
  --predictions-out data/processed/threshold_warning_l0_l2_predictions.parquet \
  --hgb-max-iter 50
```

Generated Parquets remain ignored:

- `data/interim/threshold_warning_table_v1.parquet`
- `data/processed/threshold_warning_l0_l2_predictions.parquet`

Tracked reports:

- `reports/analysis/knee/threshold_warning_qa_report.json`
- `reports/analysis/knee/threshold_warning_class_balance.csv`
- `reports/analysis/knee/threshold_warning_split_coverage.csv`
- `reports/baselines/threshold_warning_l0_l2_report.json`
- `reports/baselines/threshold_warning_l0_l2/leaderboard.csv`
- `reports/baselines/threshold_warning_l0_l2/baseline_summary.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_leakage_audit.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_claim_readiness.md`

## Warning Table QA

The prospective warning table contains 3,827 rows across 228 cells and 76
parameter sets. The threshold event is observed for 2,433 rows and censored or
not yet reached for 1,394 rows.

Class balance:

| Target | Positive rows | Positive rate |
|---|---:|---:|
| `event_within_1_checkup` | 173 | 0.045205 |
| `event_within_2_checkups` | 346 | 0.090410 |
| `event_within_3_checkups` | 494 | 0.129083 |

The QA report passes without sparse-positive warnings under the current
thresholds, but `event_within_1_checkup` is still relatively sparse and should
be treated cautiously.

## Baseline Results

Models in the initial 2.6 run:

- `B0_event_rate_prior`
- `B1_logistic_regression`
- `B2_ridge_logistic`
- `B3_hist_gradient_boosting_classifier`

Milestone 2.6.1 later renamed the HGB classifier to
`B6_hist_gradient_boosting_classifier` after adding proximity baselines. The
metric values below are unchanged for the HGB W2 rows.

Feature groups:

- `W0_capacity_state`
- `W1_state_time`
- `W2_nominal`

Mean grouped leaderboard rows:

| Target | Baseline | Mean AUROC | Mean AUPRC | Mean Brier |
|---|---|---:|---:|---:|
| `event_within_1_checkup` | B0 prior | 0.500000 | 0.073849 | 0.058275 |
| `event_within_1_checkup` | HGB + W2 | 0.970152 | 0.804752 | 0.030353 |
| `event_within_2_checkups` | B0 prior | 0.500000 | 0.145947 | 0.110646 |
| `event_within_2_checkups` | HGB + W2 | 0.938468 | 0.792906 | 0.052574 |
| `event_within_3_checkups` | B0 prior | 0.500000 | 0.181899 | 0.145791 |
| `event_within_3_checkups` | HGB + W2 | 0.939121 | 0.791905 | 0.065575 |

C-rate holdout also has enough positives for the primary 3-check-up horizon:
80 positives and 77 negatives. For that fold, HGB + W2 improves Brier from
0.407317 for the event-rate prior to 0.159930, with AUROC 0.940341 and AUPRC
0.946054.

## Claim Readiness

| Claim area | Status |
|---|---|
| Threshold label stability | `partially_supported` |
| Warning baseline feasibility | `partially_supported` |
| Grouped warning performance | `exploratory_only` |
| C-rate warning performance | `exploratory_only` |
| Calibration | `not_supported` |
| Detector-knee prediction | `blocked` |
| Policy ranking | `blocked` |

## Decision

`capacity_below_80pct_initial` is usable as a diagnostic threshold-warning
target. The 3-check-up horizon is the most balanced initial target, though
all three horizons are reported. Non-neural HGB baselines beat event-rate
priors under grouped validation, including the C-rate holdout.

The authorized statement is narrow:

> Non-neural baselines can forecast the 80% capacity-relative threshold event
> diagnostically under grouped validation using check-up-k state and nominal
> metadata.

Do not claim calibrated risk, detector-knee prediction, policy ranking,
causality, same-cell counterfactuals, or CBAT readiness.

## Remains Blocked

- detector-knee prediction
- calibrated risk claims
- neural models
- sequence models
- transformers
- CBAT
- policy ranking
- causal/mechanistic claims
- same-cell counterfactual claims
