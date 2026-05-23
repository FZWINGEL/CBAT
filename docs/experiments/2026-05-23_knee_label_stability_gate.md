# Milestone 2.5: Knee-Label Stability and Degradation-Acceleration Gate

Date: 2026-05-23

## Scope

Milestone 2.5 evaluates whether degradation-knee labels are stable enough to
support a future probabilistic knee-warning task. This is a label-stability and
target-readiness milestone only. It does not authorize knee prediction models,
neural models, sequence models, transformers, CBAT, policy ranking,
causal/mechanistic claims, or same-cell counterfactual claims.

## Commands

```bash
mbp analysis knee-labels \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/analysis/knee \
  --candidate-out data/interim/knee_candidate_table_v1.parquet

mbp analysis build-knee-risk-labels \
  --knee-candidates data/interim/knee_candidate_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/knee_risk_label_table_v1.parquet
```

Generated Parquets remain ignored:

- `data/interim/knee_candidate_table_v1.parquet`
- `data/interim/knee_risk_label_table_v1.parquet`

Tracked reports:

- `reports/analysis/knee/knee_detector_agreement.csv`
- `reports/analysis/knee/knee_label_stability_report.json`
- `reports/analysis/knee/knee_by_condition.csv`
- `reports/analysis/knee/knee_replicate_consistency.csv`
- `reports/analysis/knee/knee_claim_readiness.md`

## Detectors

Implemented detectors:

- `piecewise_linear_bic`
- `max_chord_distance`
- `two_line_l_method`
- `slope_change_threshold`
- `capacity_threshold_80`
- `capacity_threshold_70`
- `capacity_threshold_60`

Sensitivity axes:

- x-axis: `checkup_index`, `calendar_days`, `log_age_efc_cumulative`
- smoothing: `none`, `rolling_3`

The primary candidate policy is `piecewise_linear_bic` on `checkup_index` with
no smoothing.

## Results

Real-data output:

| Area | Result |
|---|---:|
| Cells | 228 |
| Candidate rows | 9,576 |
| Valid candidate rows | 6,747 |
| Primary candidate rows | 228 |
| Primary valid rows | 189 |
| Exploratory risk-label rows | 3,827 |

Trajectory QA:

| Area | Count |
|---|---:|
| Few-checkup cells | 39 |
| Cells with capacity increases > 0.02 Ah | 6 |

Sensitivity:

| Sensitivity | Median disagreement | Agreement within 2 check-ups | Comparisons |
|---|---:|---:|---:|
| x-axis | 0 | 0.892397 | 2,249 |
| smoothing | 0 | 0.951068 | 3,372 |

Replicate consistency is the main blocker. For the primary detector/x-axis/no
smoothing policy, 64 parameter-set conditions have valid replicate knee rows,
and 45 are consistent within 2 check-ups. That fraction, 0.703, is not strong
enough for a knee-prediction milestone.

Exploratory interval labels:

| Label | Positive rows | Total rows |
|---|---:|---:|
| `knee_within_1_checkup` | 189 | 3,827 |
| `knee_within_2_checkups` | 378 | 3,827 |
| `knee_within_3_checkups` | 558 | 3,827 |

These labels are exploratory only.

## Claim Readiness

| Claim area | Status |
|---|---|
| Detector stability | `partially_supported` |
| X-axis robustness | `partially_supported` |
| Smoothing robustness | `partially_supported` |
| Replicate consistency | `not_supported` |
| Early-warning label readiness | `exploratory_only` |
| Prediction readiness | `blocked` |

## Decision

Knee labels are not stable enough to authorize knee-risk prediction. The
current detector suite provides useful exploratory diagnostics, and the primary
detector labels most cells, but replicate-triplet consistency fails the gate.

Do not open a knee prediction milestone yet. A future knee track should either:

- narrow the claim scope to conditions with stable replicate knees;
- improve/justify detector policy before modeling;
- or treat threshold-event labels separately from knee labels.

## Remains Blocked

- knee prediction models
- neural models
- sequence models
- transformers
- CBAT
- policy ranking
- causal/mechanistic claims
- same-cell counterfactual claims
