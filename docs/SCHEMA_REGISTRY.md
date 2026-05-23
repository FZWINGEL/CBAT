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
| `pulse_qa_report` | Implemented | `mbp.data.products.pulse_targets` | PULSE summary path, check-up table path, canonical target policy, coverage CSV, alignment report |
| `pulse_target_table` | Implemented | `mbp.data.products.pulse_targets` | PULSE summary path, interval table path, canonical SOC/temperature context, policy version, schema version |
| `pulse_alignment_sensitivity_report` | Implemented | `mbp.data.products.pulse_targets` | PULSE summary path, pulse target table path, interval table path, canonical context, alignment thresholds, retained coverage |
| `pulse_missingness_reports` | Implemented | `mbp.data.products.pulse_targets` | PULSE target table path, interval table path, missing endpoint rows, condition groupings, split groupings |
| `pulse_resistance_baseline_report` | Implemented | `mbp.baselines.pulse` | interval table path, interval subset registry path, PULSE target table path, optional stress-feature sidecar, grouped split view, target coverage |
| `pulse_target_robustness_report` | Implemented | `mbp.baselines.pulse` | PULSE baseline report path, scalar target list, grouped split view, 1s/10ms comparisons, delta/k1 comparisons, claim-readiness memo |
| `capacity_pulse_coupling_table` | Implemented | `mbp.coupling.pulse_capacity` | interval table path, PULSE target table path, canonical target policy, schema version |
| `pulse_capacity_coupling_diagnostics` | Implemented | `mbp.coupling.pulse_capacity` | capacity report path, capacity prediction path, interval table path, PULSE target table path, residual/PULSE-growth correlation outputs |
| `pulse_capacity_coupling_robustness` | Implemented | `mbp.coupling.pulse_capacity` | canonical model/feature/target selection, interval-level aggregation, condition-level aggregation, parameter-set bootstrap, residualized confound-control diagnostics |
| `prior_pulse_capacity_predictive_comparison` | Implemented | `mbp.baselines.capacity` | capacity baseline report, prior-PULSE capacity report, paired condition-level gains, parameter-set bootstrap, coverage effects, leakage audit |
| `prior_pulse_vs_best_nonpulse_comparison` | Implemented | `mbp.baselines.capacity` | non-PULSE capacity reports, prior-PULSE capacity report, PULSE-covered interval restriction, strongest non-PULSE group selection, paired gains, bootstrap intervals |
| `eis_qa_report` | Implemented | `mbp.data.products.eis_features` | EIS table path, spectrum-quality path, interval table path, coverage CSV, alignment report, valid-frequency mask audit |
| `eis_feature_table_v1` | Implemented | `mbp.data.products.eis_features` | EIS table path, spectrum-quality path, interval table path, canonical SOC/temperature context, feature policy version, schema version |
| `eis_feature_qa_report` | Implemented | `mbp.data.products.eis_features` | EIS feature table path, interval table path, selected-frequency completeness, feature NaN counts, split coverage |
| `eis_claim_readiness` | Implemented | `mbp.data.products.eis_features` | EIS QA report, EIS feature QA report, feature policy status, blocked predictive claims |
| `eis_target_table_v1` | Implemented | `mbp.data.products.eis_features` | EIS feature table path, interval table path, canonical SOC/temperature context, k/k1 feature availability, delta EIS targets, feature policy version |
| `eis_scalar_baseline_report` | Implemented | `mbp.baselines.eis` | interval table path, interval subset registry path, EIS target table path, grouped split view, target coverage, leakage audit |
| `prior_eis_vs_best_noneis_comparison` | Implemented | `mbp.baselines.eis_claims` | non-EIS report paths, prior-EIS report path, EIS target table path, same-population filters, paired condition gains, parameter-set bootstrap intervals |
| `eis_alignment_feature_sensitivity` | Implemented | `mbp.baselines.eis_claims` | EIS target table path, prior-EIS/non-EIS report paths, alignment thresholds, feature-completeness filters, retained coverage counts |
| `eis_leakage_audit` | Implemented | `mbp.baselines.eis_claims` | capacity/PULSE/EIS feature group definitions, prior-EIS allowlist, future EIS/R0R1/DRT/embedding blocklist |
| `semi_empirical_capacity_report` | Implemented | `mbp.baselines.semi_empirical` | interval table path, interval subset registry path, stress-feature sidecar path, SE0-SE4 feature policy, grouped split view |
| `replicate_uncertainty_diagnostics` | Implemented | `mbp.analysis.replicate_uncertainty` | interval table path, capacity report path, capacity prediction path, condition-triplet spread, empirical tolerance intervals |

## Gate 2/3 Schema Contracts

- `MODALITY_TABLE_LOG_AGE_SCHEMA` contains reduced operating-log signals plus nullable inserted diagnostics. The inserted diagnostic values are not interval features by default.
- `CONDITION_TABLE_SCHEMA` includes `voltage_window_family`, derived from cyclic voltage limits or calendar idle SOC, so voltage/SOC-window holdouts no longer rely on scalar `age_soc`.
- `INTERVAL_TABLE_SCHEMA` is one row per adjacent `checkup_event_table` transition. It includes condition metadata, split labels, prior/post capacity targets, LOG_AGE exposure summaries, masked diagnostic-row counts, monotonicity violation counts/drop magnitudes, `LOG_AGE_monotonicity_clean`, quality flags, and schema provenance.
- `SPLIT_REGISTRY_SCHEMA` keeps replicates of each 76-parameter condition triplet grouped for headline validation and includes `voltage_window_holdout_fold`. The legacy `soc_window_holdout_fold` is retained as a compatibility alias populated from the corrected voltage-window semantics.
- `INTERVAL_SUBSET_REGISTRY_SCHEMA` defines strict/tolerant clean interval labels, sensitivity flags, exclusion reasons, and the monotonicity policy version used for baseline readiness.
- `INTERVAL_STRESS_FEATURES_SCHEMA` is a modular sidecar keyed by `cell_id`, `checkup_k`, and `checkup_k_next`. It contains LOG_AGE-derived scalar dwell, current, SOC, coupled-stress, coverage/gap, event-segmented, and diagnostic normalized-rate fields. Target-derived normalized-rate fields are excluded from F5-F13 predictive feature groups.
- `BASELINE_PREDICTION_SCHEMA` records row-level capacity predictions for the Milestone 0.5 baseline ladder and later capacity-only diagnostics. Normalized delta-rate target modes are evaluated back in `delta_capacity_Ah` units. The JSON report aggregates metrics by held-out parameter-set condition; generated prediction Parquet remains ignored by default. The report renderer also emits leaderboard CSV, baseline summary markdown, evaluation-card JSON files, diagnostic markdown, C-rate error analysis, rate-target comparisons, train-fold bias-correction tables, and plot-ready CSV tables.
- `PULSE_TARGET_TABLE_SCHEMA` is one row per interval for the canonical PULSE target context. It records RT/50% SOC resistance at check-up `k` and `k+1`, resistance deltas, alignment deltas, quality flags, schema version, and target direction handling in metadata. The canonical direction handling is currently `mean`; `charge` and `discharge` sidecars are diagnostic.
- `pulse_alignment_sensitivity_report` records canonical alignment-delta summaries and retained interval/cell/parameter-set/split coverage under 6h, 12h, 24h, 36h, and all-row thresholds.
- `pulse_missingness_reports` record missing canonical PULSE endpoints by interval, parameter-set condition, C-rate holdout fold, and profile holdout fold.
- `PULSE_PREDICTION_SCHEMA` records row-level scalar PULSE resistance baseline predictions. Generated prediction Parquet remains ignored by default; JSON/CSV/markdown report artifacts are trackable.
- `pulse_target_robustness_report` reuses the scalar PULSE baseline report schema and adds rendered comparison CSVs for target family, 1s-vs-10ms behavior, and delta-vs-k1 behavior.
- `capacity_pulse_coupling_table` is one row per interval with finite capacity targets and canonical PULSE targets. It includes condition metadata, split labels, LOG_AGE EFC/calendar controls, quality flags, and schema version.
- `pulse_capacity_coupling_diagnostics` joins capacity prediction residuals to canonical PULSE growth and reports Pearson/Spearman correlations plus grouped C-rate/cold-rate summaries. It is a prediction-row diagnostic only and does not authorize multimodal claims.
- `pulse_capacity_coupling_robustness` filters to one canonical capacity model/feature/target, then reports interval-level and condition-level correlations, parameter-set bootstrap summaries, residualized confound-control correlations, subgroup summaries, and coupling claim-readiness.
- `prior_pulse_capacity_predictive_comparison` compares F4 against the best prior-PULSE feature group on the same PULSE-covered interval population. It reports paired condition-level gains, split-level bootstrap intervals, coverage effects, and claim-readiness. Future PULSE state and PULSE deltas are forbidden as capacity inputs.
- `prior_pulse_vs_best_nonpulse_comparison` compares the best prior-PULSE HGB group against the strongest supplied non-PULSE HGB group by target/split on the same PULSE-covered interval population. It reports paired condition-level gains, bootstrap intervals, and claim-readiness.
- `EIS_FEATURE_TABLE_V1_SCHEMA` is one row per cell/check-up/SOC/temperature context for the canonical EIS feature policy. The v1 sidecar records selected-frequency E1 features, nullable R0/R1 placeholders with explicit provenance/leakage fields, E3 geometric Nyquist summaries, valid-frequency coverage, alignment delta, quality flags, schema version, and feature policy version.
- `eis_qa_report` audits EIS coverage by SOC, RT/OT context, cell, check-up, and split metadata; reports valid modeling frequency/fraction distributions; writes alignment summaries; and verifies the charter mask excludes 100 Hz, 208.3 Hz, and 14.7 kHz while retaining finite valid 0.5-5000 Hz values.
- `eis_feature_qa_report` checks the canonical RT/50% feature table for row/cell/condition coverage, selected-frequency completeness, feature NaN counts, valid modeling fraction, split coverage, and warnings. It does not authorize EIS predictive claims.
- `EIS_TARGET_TABLE_V1_SCHEMA` is one row per interval with canonical RT/50 EIS features at check-up `k` and `k+1`, EIS delta targets, valid modeling fractions, alignment deltas, split labels, quality flags, schema version, and feature policy version. Future EIS `k1` features and EIS deltas are forbidden as capacity/PULSE inputs.
- `eis_scalar_baseline_report` records grouped scalar EIS endpoint baselines for selected-frequency and geometric Nyquist targets. It is an EIS self-diagnostic baseline and does not by itself authorize EIS improvement claims.
- `prior_eis_vs_best_noneis_comparison` compares best prior-EIS PULSE/capacity HGB groups against strongest supplied non-EIS HGB groups on the same EIS-covered prediction population. It reports paired condition-level gains, parameter-set bootstrap intervals, C-rate summaries, and conservative claim-readiness.
- `eis_alignment_feature_sensitivity` records whether 24 h/36 h EIS alignment thresholds and selected-frequency/valid-fraction filters change prior-EIS comparison conclusions.
- `eis_leakage_audit` confirms non-EIS target baselines use only prior EIS `k` scalar features and exclude EIS `k1`, EIS deltas, R0/R1 without leakage-safe provenance, DRT fields, and learned embeddings.
- `semi_empirical_capacity_report` records non-neural ridge-style semi-empirical stress comparators. Generated prediction Parquet remains ignored; JSON/CSV/Markdown reports are trackable.
- `replicate_uncertainty_diagnostics` records condition-triplet spread, empirical min/max tolerance intervals, model error versus replicate spread, C-rate replicate uncertainty, and conservative uncertainty claim-readiness.
