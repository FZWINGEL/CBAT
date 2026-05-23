# Milestone 2.4: Temporal History Value and Run-Event Data Product Gate

Date: 2026-05-23

## Scope

Milestone 2.4 tests whether ordered LOG_AGE operational event structure adds
predictive value beyond scalar and histogram exposure summaries. This is a
falsification gate before any sequence model. It does not authorize neural
models, transformers, CBAT, policy ranking, capacity+PULSE+EIS architecture
work, causal/mechanistic claims, or sequence-model readiness claims.

## Commands

```bash
mbp features build-run-events \
  --log-age data/interim/modality_table_log_age.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/run_event_table_v1.parquet \
  --progress-interval 25000

mbp features run-events-qa \
  --run-events data/interim/run_event_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/run_event_qa_report.json \
  --coverage-out reports/audit/run_event_coverage.csv

mbp features build-sequence-features \
  --run-events data/interim/run_event_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/interval_sequence_features_v1.parquet \
  --seed 42

mbp features sequence-qa \
  --sequence-features data/interim/interval_sequence_features_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/sequence_feature_qa_report.json

mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --sequence-features data/interim/interval_sequence_features_v1.parquet \
  --out reports/baselines/capacity_sequence_value_hgb50_report.json \
  --predictions-out data/processed/capacity_sequence_value_hgb50_predictions.parquet \
  --report-dir reports/baselines/capacity_sequence_value_hgb50 \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress,F14_event_aggregate,F15_event_order_aware,F16_event_order_shuffled,F17_event_order_plus_stress \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50

mbp baseline diagnose-sequence-value \
  --report reports/baselines/capacity_sequence_value_hgb50_report.json \
  --baseline-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --out-dir reports/baselines/capacity_sequence_value_hgb50
```

## Data Products

The run-event builder streamed the full LOG_AGE table row-group by row-group and
wrote completed event rows in Parquet batches. It did not materialize the
904,977,105-row LOG_AGE table or the event table in memory.

Real-data output:

- interval-window LOG_AGE rows processed: 899,831,845
- run-event rows written: 79,328,229
- intervals covered: 3,827 / 3,827
- sequence-feature rows written: 3,827

The large Parquet outputs remain ignored generated artifacts:

- `data/interim/run_event_table_v1.parquet`
- `data/interim/interval_sequence_features_v1.parquet`
- `data/processed/capacity_sequence_value_hgb50_predictions.parquet`

## QA Results

Run-event QA is warning-level, not clean-pass:

- `row_count`: 79,328,229
- `intervals_covered`: 3,827
- `missing_intervals`: 0
- `duration_delta_gt_24h_intervals`: 751
- event counts:
  - charge: 24,892,072
  - discharge: 31,308,489
  - rest: 23,127,668

The duration mismatch warning is important. Event coverage is complete, but
event-duration sums can differ materially from interval durations. This limits
any claim that the v1 event table is a publication-ready reconstruction of
physical duty-cycle duration. The v1 table is adequate for a temporal-value
falsification diagnostic, not for a strong operational-event claim.

Sequence-feature QA passed:

- `row_count`: 3,827
- `missing_intervals`: 0
- `nan_counts`: none
- `shuffle_seed`: 42
- target-derived capacity-rate leakage check: passed

## Sequence-Value Results

Positive gain means the candidate has lower condition-mean MAE than the
reference.

| Comparison | Status | Mean gain | Positive rows |
|---|---|---:|---:|
| Order-aware vs aggregate event features | not supported | -0.000575091 | 13 / 24 |
| Order-aware vs shuffled-order controls | not supported | -0.000564409 | 12 / 24 |
| Order-aware plus stress vs timestamp-weighted stress | not supported | -0.000470028 | 8 / 24 |
| C-rate order-aware improvement | not supported | -0.00131991 | 1 / 4 |

C-rate details:

| Target | Comparison | Gain |
|---|---|---:|
| `capacity_Ah_k1` | order vs aggregate | 0.00129804 |
| `delta_capacity_Ah` | order vs aggregate | -0.00328221 |
| `capacity_Ah_k1` | order vs shuffled | 0.00823437 |
| `delta_capacity_Ah` | order vs shuffled | -0.00348868 |
| `capacity_Ah_k1` | order plus stress vs stress | -0.00551325 |
| `delta_capacity_Ah` | order plus stress vs stress | -0.00451210 |

Profile and some temperature rows show positive descriptive gains, but the
overall grouped evidence does not pass the sequence-value gate because
order-aware features do not consistently beat aggregate or shuffled controls
and do not improve the stress baseline overall.

## Decision

Run events are reproducible and coverage-complete, but v1 duration QA is
warning-level. Aggregate event and order-aware features are useful diagnostics,
but order-aware features do not beat aggregate-only features, shuffled-order
controls, or the existing timestamp-weighted stress baseline overall.

No non-neural sequence-summary claim is authorized. A later sequence model is
not justified by Milestone 2.4.

## Remaining Blocked

- neural sequence models
- transformers
- CBAT
- DRT
- EIS embeddings
- policy ranking
- capacity+PULSE+EIS architecture work
- causal/mechanistic claims
- broad temporal-order claims

## Engineering Follow-Up

The memory-safe run-event builder is still slow because it orchestrates 257,311
small Parquet row groups in one process. A future engineering-only speedup
should precompact or index LOG_AGE into larger cell-partitioned chunks and then
reuse the same event definitions. That would improve runtime without changing
the scientific result definition.
