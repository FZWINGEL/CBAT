# Schema Registry

Schema version prefix: `gate1.audit.v1`

| Data product | Status | Owner module | Required provenance |
|---|---|---|---|
| `file_inventory` | Implemented | `mbp.audit.inventory` | data root, tool, generated timestamp, schema version, SHA-256 |
| `DATASET_MANIFEST.json` | Implemented | `mbp.audit.manifest` | data root, tool version, preprocessing commit, generated timestamp |
| `MANIFEST.sha256` | Implemented | `mbp.audit.manifest` | relative path and SHA-256 per observed file |
| `modality_coverage.csv` | Placeholder implemented | `mbp.audit.coverage` | modality family, observed files, rows, status |
| `known_issues.csv` | Placeholder implemented | `mbp.audit.known_issues` | issue ID, severity, status, evidence |
| `cell_condition_table` | Implemented | `mbp.data.luh_blank.parse_cfg` | source files, parser version, schema version, voltage-window family |
| `checkup_event_table` | Implemented | `mbp.data.luh_blank.parse_eoc` | source files, parser version, schema version |
| `run_event_table` | Not implemented | `mbp.data.products.run_event_table` | source files, parser version, schema version |
| `modality_table_eis` | Implemented | `mbp.data.luh_blank.parse_eis` | source files, parser version, EIS validity masks |
| `modality_table_pulse` | Implemented | `mbp.data.luh_blank.parse_pulse` | source files, parser version, pulse provenance |
| `modality_table_log_age` | Implemented | `mbp.data.luh_blank.parse_log` | source archive, source file, cohort exclusion report, diagnostic masking rules |
| `split_registry_v1` | Implemented | `mbp.data.splitting` | condition table, deterministic seed, grouped parameter-set folds, voltage-window holdout |
| `interval_table` | Implemented MVP | `mbp.data.products.interval_table` | joined inputs, split registry SHA-256, LOG_AGE row-group exposure scan, monotonicity report path, leakage checks |
| `interval_subset_registry_v1` | Implemented | `mbp.data.products.interval_subsets` | interval table path, LOG_AGE monotonicity policy version, EFC jitter threshold, schema version |
| `interval_stress_features_v1` | Implemented | `mbp.data.products.stress_features` | interval table path, LOG_AGE path, row-group stress scan, feature policy version, current-sign policy |
| `current_sign_audit_report` | Implemented | `mbp.data.products.current_sign_audit` | LOG_AGE path, interval table path, streamed row-group derivative evidence, sign convention recommendation |
| `interval_stress_features_v1_1` | Implemented | `mbp.data.products.stress_features` | interval table path, LOG_AGE path, timestamp-weighted row-group stress scan, coverage/gap diagnostics, event summaries, feature policy version, current-sign policy |
| `capacity_baseline_predictions` | Implemented | `mbp.baselines.capacity` | interval table path, interval subset registry path, split view, subset, model level, feature group, schema version |
| `capacity_baseline_report` | Implemented | `mbp.baselines.capacity` | interval table path, interval subset registry path, optional stress-feature sidecar path, subset, model level, feature group, split view, strict/tolerant sensitivity scope |
| `capacity_baseline_diagnostics` | Implemented | `mbp.baselines.capacity` | baseline report path, optional L0 reference report path, feature-gain diagnostics, best-by-target/split rows, C-rate holdout condition/grouped errors, claim-readiness memo, quantile metrics |
| `stress_feature_diagnostics` | Implemented | `mbp.baselines.capacity` | stress-feature baseline report path, HGB-50 F4 baseline report path, L0 reference report path, C-rate success criteria |
| `target_consistency_diagnostics` | Implemented | `mbp.baselines.capacity` | capacity report path, prediction Parquet path, interval-table join, direct-vs-derived target metrics, C-rate residual groupings, stress-feature ablation gains |
| `c_rate_delta_failure_diagnostics` | Implemented | `mbp.baselines.capacity` | normalized delta-rate target report, train-fold residual correction report, narrow F11-F13 feature report, direct F4 threshold comparison |

## Gate 2/3 Schema Contracts

- `MODALITY_TABLE_LOG_AGE_SCHEMA` contains reduced operating-log signals plus nullable inserted diagnostics. The inserted diagnostic values are not interval features by default.
- `CONDITION_TABLE_SCHEMA` includes `voltage_window_family`, derived from cyclic voltage limits or calendar idle SOC, so voltage/SOC-window holdouts no longer rely on scalar `age_soc`.
- `INTERVAL_TABLE_SCHEMA` is one row per adjacent `checkup_event_table` transition. It includes condition metadata, split labels, prior/post capacity targets, LOG_AGE exposure summaries, masked diagnostic-row counts, monotonicity violation counts/drop magnitudes, `LOG_AGE_monotonicity_clean`, quality flags, and schema provenance.
- `SPLIT_REGISTRY_SCHEMA` keeps replicates of each 76-parameter condition triplet grouped for headline validation and includes `voltage_window_holdout_fold`. The legacy `soc_window_holdout_fold` is retained as a compatibility alias populated from the corrected voltage-window semantics.
- `INTERVAL_SUBSET_REGISTRY_SCHEMA` defines strict/tolerant clean interval labels, sensitivity flags, exclusion reasons, and the monotonicity policy version used for baseline readiness.
- `INTERVAL_STRESS_FEATURES_SCHEMA` is a modular sidecar keyed by `cell_id`, `checkup_k`, and `checkup_k_next`. It contains LOG_AGE-derived scalar dwell, current, SOC, coupled-stress, coverage/gap, event-segmented, and diagnostic normalized-rate fields. Target-derived normalized-rate fields are excluded from F5-F13 predictive feature groups.
- `BASELINE_PREDICTION_SCHEMA` records row-level capacity predictions for the Milestone 0.5 baseline ladder and later capacity-only diagnostics. Normalized delta-rate target modes are evaluated back in `delta_capacity_Ah` units. The JSON report aggregates metrics by held-out parameter-set condition; generated prediction Parquet remains ignored by default. The report renderer also emits leaderboard CSV, baseline summary markdown, evaluation-card JSON files, diagnostic markdown, C-rate error analysis, rate-target comparisons, train-fold bias-correction tables, and plot-ready CSV tables.
