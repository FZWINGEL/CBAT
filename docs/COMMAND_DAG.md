# Benchmark Command DAG

This DAG documents the current release-candidate dependency structure. It is a
human-readable command map; generated data products remain local ignored
artifacts.

```text
Layer 0: Raw archives and metadata
  data/raw/*
    |
    v
Layer 1: Audit
  mbp audit manifest
  mbp audit result-data
  mbp audit split-registry
    |
    v
Layer 2: Ingested modality tables
  mbp ingest eoc
  mbp ingest pulse
  mbp ingest eis
  mbp ingest log-age
    |
    v
Layer 3: Core interval and split products
  mbp intervals build
  mbp split interval-subsets
    |
    v
Layer 4: Feature and target sidecars
  mbp features build-stress
  mbp features build-run-events
  mbp features build-sequence-features
  mbp pulse build-targets
  mbp eis build-features
  mbp eis build-targets
  mbp analysis knee-labels
  mbp analysis threshold-event-labels
  mbp analysis build-threshold-warning-table
  mbp analysis build-capacity-horizon-table
  mbp analysis build-capacity-horizon-trajectory-features
    |
    v
Layer 5: Baseline reports
  mbp baseline run-capacity
  mbp baseline run-pulse
  mbp baseline run-eis
  mbp baseline run-semi-empirical
  mbp baseline run-threshold-warning
  mbp baseline run-stressor-robust-capacity
  mbp baseline run-stressor-robust-pareto
  mbp baseline run-stressor-robust-adaptive
  mbp baseline replicate-stressor-robust-adaptive
  mbp baseline run-stressor-robust-attribution
  mbp baseline run-stressor-robust-arm-selector
  mbp baseline run-hierarchical-capacity
  mbp baseline run-capacity-horizon
    |
    v
Layer 6: Diagnostics and hardening
  mbp analysis replicate-uncertainty
  mbp analysis calibrate-capacity
  mbp analysis capacity-horizon-qa
  mbp analysis capacity-horizon-trajectory-qa
  mbp baseline diagnose-capacity-horizon
  mbp baseline diagnose-capacity-horizon-trajectory
  mbp baseline diagnose-sequence-value
  mbp baseline compare-prior-eis-pulse
  mbp baseline compare-prior-eis-capacity
  mbp baseline compare-threshold-warning-censoring
  mbp baseline finalize-threshold-warning-claim
  mbp baseline diagnose-stressor-robust-forensics
    |
    v
Layer 7: Synthesis and release checks
  docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md
  reports/synthesis/main_project_claim_matrix_v2.csv
  reports/synthesis/main_project_gate_status.md
  reports/synthesis/blocked_claims_v2.md
  reports/synthesis/next_branch_decision.md
  reports/synthesis/artifact_manifest_v2.csv
  reports/synthesis/release_candidate_check.md
  configs/benchmark_tasks_v1.yaml
  mbp report check-benchmark-tasks
  reports/synthesis/benchmark_task_registry_check.md
  reports/synthesis/benchmark_leaderboard_v1.csv
  reports/synthesis/benchmark_task_cards_v1.md
  reports/synthesis/benchmark_model_cards_v1.md
```

## Key Dependency Rules

- `interval_table.parquet` is the parent product for grouped validation,
  feature sidecars, target sidecars, diagnostics, and synthesis.
- `interval_subset_registry_v1.parquet` is required for grouped baseline
  evidence.
- LOG_AGE-derived transition/stress sidecars must not enter prospective
  threshold-warning features unless they are explicitly prior-only.
- PULSE and EIS non-EIS target runs may use prior check-up `k` state only.
- Prediction Parquets are local generated artifacts and must not be committed.
