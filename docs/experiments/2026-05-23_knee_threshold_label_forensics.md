# Milestone 2.5.1: Knee Label Forensics and Threshold-Event Alternative Gate

Date: 2026-05-23

## Scope

Milestone 2.5.1 explains why primary detector-knee labels failed replicate
consistency, defines a stable-condition registry, and evaluates whether
threshold-event labels are more stable than detector knees. This is a label and
target-readiness milestone only. It does not train or authorize knee prediction
models, neural models, sequence models, transformers, CBAT, policy ranking,
causal/mechanistic claims, or same-cell counterfactual claims.

## Commands

```bash
mbp analysis knee-forensics \
  --knee-candidates data/interim/knee_candidate_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/analysis/knee

mbp analysis knee-stable-registry \
  --knee-candidates data/interim/knee_candidate_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/knee_stable_condition_registry_v1.parquet \
  --report reports/analysis/knee/knee_stable_condition_report.json \
  --coverage-out reports/analysis/knee/knee_stable_condition_coverage.csv

mbp analysis threshold-event-labels \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/analysis/knee \
  --labels-out data/interim/threshold_event_label_table_v1.parquet

mbp analysis knee-vs-threshold \
  --knee-candidates data/interim/knee_candidate_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/analysis/knee/knee_vs_threshold_decision.md
```

Generated Parquets remain ignored:

- `data/interim/knee_stable_condition_registry_v1.parquet`
- `data/interim/threshold_event_label_table_v1.parquet`

Tracked reports:

- `reports/analysis/knee/knee_inconsistent_conditions.csv`
- `reports/analysis/knee/knee_inconsistency_forensics.md`
- `reports/analysis/knee/knee_stable_condition_report.json`
- `reports/analysis/knee/knee_stable_condition_coverage.csv`
- `reports/analysis/knee/threshold_event_stability.csv`
- `reports/analysis/knee/threshold_event_by_condition.csv`
- `reports/analysis/knee/threshold_event_claim_readiness.md`
- `reports/analysis/knee/knee_vs_threshold_decision.md`

## Knee Forensics

Primary detector policy:

- detector: `piecewise_linear_bic`
- x-axis: `checkup_index`
- smoothing: `none`

Milestone 2.5 found 64 primary-valid parameter-set conditions and only 45
were replicate-consistent within 2 check-ups. Milestone 2.5.1 identifies the
remaining 19 inconsistent primary-valid conditions.

The stable-condition registry applies this default rule:

- primary detector valid for at least 2 replicates;
- knee spread no greater than 2 check-ups;
- no severe trajectory QA flags.

Real-data registry result:

| Status | Conditions |
|---|---:|
| stable | 40 |
| unstable | 23 |
| insufficient-label | 13 |
| total | 76 |

Stable fraction is 0.526, so the stable-knee subset is useful for diagnostics
but too narrow for a detector-knee prediction claim.

## Threshold Events

Threshold labels were generated for SOH/capacity-relative crossings at 80%,
70%, and 60%. The capacity-relative and SOH variants are equivalent under the
current initial-capacity SOH definition, but both names are emitted to make the
label policy explicit.

| Threshold label | Cell coverage | Condition coverage | Consistency within 2 check-ups | Median event check-up |
|---|---:|---:|---:|---:|
| `capacity_below_80pct_initial` | 0.759 | 0.763 | 0.897 | 8 |
| `capacity_below_70pct_initial` | 0.588 | 0.592 | 0.867 | 10 |
| `capacity_below_60pct_initial` | 0.390 | 0.434 | 0.909 | 13 |

The current target-readiness policy selects `capacity_below_80pct_initial`
because it passes the consistency threshold while retaining the broadest
condition coverage.

## Knee vs Threshold Decision

Primary detector-knee replicate consistency within 2 check-ups is 0.703.
The best threshold-event label, `capacity_below_80pct_initial`, has replicate
consistency within 2 check-ups of 0.897 and condition coverage of 0.763.

Threshold events are therefore more stable than detector knees in this
diagnostic. They are still threshold degradation milestones, not validated
prediction targets. A future early-warning task must separately test timing,
prevalence, grouped validation, calibration, and baseline performance.

## Claim Readiness

| Claim area | Status |
|---|---|
| Detector-knee prediction readiness | `blocked` |
| Stable-knee subset readiness | `diagnostic_only` |
| Threshold-event label stability | `partially_supported` |
| Threshold-event warning usefulness | `diagnostic_only` |
| Threshold-event prediction readiness | `possible_next_gate` |

## Decision

Do not open detector-knee prediction. Detector-based knee labels remain
diagnostic/exploratory because replicate consistency fails and the stable
subset covers only 40 / 76 conditions.

A later narrow non-neural milestone may evaluate threshold-event early-warning
baselines, with `capacity_below_80pct_initial` as the current best candidate
label. That future milestone must still use grouped validation and must not
claim policy ranking, causality, CBAT readiness, or same-cell counterfactuals.

## Remains Blocked

- detector-knee prediction
- neural models
- sequence models
- transformers
- CBAT
- policy ranking
- causal/mechanistic claims
- same-cell counterfactual claims
