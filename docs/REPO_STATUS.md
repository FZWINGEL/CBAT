# Repository Status

Last updated: 2026-05-23

Current branch: `main`

Current commit: see `git log -1 --oneline`. This file is updated whenever
significant repository state changes happen, but it intentionally avoids a
self-referential commit hash that would become stale when the status file itself
is committed.

## Executive Summary

The repository is in **Milestone 1.1: Manuscript Draft Package v0.1**.
Gate 2b LOG_AGE integrity triage, Milestone 0.4 baseline readiness, the first
bounded Milestone 0.5 capacity baseline ladder, Milestone 0.5b robustness
diagnostics, Milestone 0.5c synthesis, and Milestone 0.6 stress-feature v1 are
complete. Milestone 0.6.1 stress-feature hardening and Milestone 0.6.2 target
consistency diagnostics are complete. Milestone 0.6.3 closed the broad
LOG_AGE-only scalar stress-feature path for the current C-rate delta problem.
Milestone 0.7 opened a scoped PULSE QA-first resistance evidence stream.
Milestone 0.7.1 hardened that stream before any PULSE scientific claim.
Milestone 0.7.2 finalized scalar target robustness and claim-readiness.
Milestone 0.8 opens controlled scalar capacity-PULSE coupling diagnostics.
Milestone 0.8.1 hardens that evidence with canonical-model filtering,
interval-level aggregation, condition-level aggregation, parameter-set bootstrap
summaries, and simple confound-control residualization.
Milestone 0.9 tests a narrow non-neural predictive claim using prior PULSE state
at check-up `k` only.
Milestone 0.9.1 compares that prior-PULSE result against the strongest supplied
non-PULSE HGB baselines on the same PULSE-covered interval population.
Milestone 1.0 consolidates the completed capacity, LOG_AGE stress-feature,
PULSE resistance, coupling, and prior-PULSE evidence into a paper-facing claim
ledger, synthesis report set, figure plan, and paper skeleton.
Milestone 1.0.1 hardens those paper-facing artifacts with wording refinements,
source-artifact checklists, reviewer-risk tracking, and manuscript packaging.
Milestone 1.1 creates a manuscript-ready draft package with prose sections,
figure/table specifications, source traceability, and reviewer response prep.

No EIS claims, PULSE scientific claims beyond scalar resistance baselines,
sequence models, neural architecture, policy ranking, CBAT architecture, or EIS
embedding work has been started.

Current state:

- LOG_AGE monotonicity policy is documented in
  `docs/LOG_AGE_MONOTONICITY_POLICY.md`.
- Interval subset registry generation is implemented with
  `mbp split interval-subsets`.
- `reports/audit/interval_subset_report.json` records strict/tolerant clean
  interval counts under policy version `log_age_monotonicity.v1`.
- Split registry semantics now include corrected voltage-window holdout folds
  derived from `voltage_window_family`, not scalar `age_soc`.
- `pyarrow`, `py7zr`, and `numpy` are core dependencies; `numpy` is required by
  vectorized stress-feature aggregation. Pandas/scikit-learn baseline packages
  and GBM packages remain optional extras.
- `mbp baseline run-capacity` implements the first L0-L3 capacity baseline
  runner and is gated by `interval_subset_registry_v1.parquet`.
- The dependency-free real-data L0 persistence smoke run completed and emitted
  trackable report artifacts under `reports/baselines/capacity_l0_smoke/`.
- The bounded full real-data L0-L3 ladder completed with `--hgb-max-iter 5` and
  emitted trackable report artifacts under `reports/baselines/capacity_l0_l3/`.
- Baseline diagnostics now exist for the full report, scaled Ridge rerun, and
  focused HGB-50 robustness rerun. Focused diagnostics can now compare against
  an L0 reference report.
- A Milestone 0.5c claim-readiness memo and synthesis note document that the
  next engineering direction should be stronger LOG_AGE-derived scalar stress
  features, not PULSE/EIS/CBAT expansion.
- Milestone 0.6 stress-feature tooling is implemented with a modular sidecar
  table, QA report, baseline join path, F5-F7 feature groups, and focused
  HGB-50 stress-feature diagnostics.
- The first non-target-derived stress-feature run produced a mixed result:
  `capacity_Ah_k1` C-rate holdout improved slightly, but `delta_capacity_Ah`
  C-rate holdout degraded versus the HGB-50 F4 baseline.
- Milestone 0.6.1 hardening has been run on real data. The current-sign audit
  gives high-confidence positive-current charge evidence, v1.1 QA passes, and
  the focused HGB-50 stress-feature run remains mixed: C-rate `capacity_Ah_k1`
  improves, but C-rate `delta_capacity_Ah` still fails to beat F4.
- Milestone 0.6.2 target-consistency diagnostics are implemented and run on the
  v1.1 report. Direct delta remains the stronger C-rate delta target path;
  deriving delta from capacity does not solve the failure.
- Milestone 0.6.3 normalized-rate target checks, train-fold bias-correction
  diagnostics, and narrow F11-F13 cold/current feature groups are implemented
  and run. None beats the F4 C-rate `delta_capacity_Ah` threshold.
- Milestone 0.7 PULSE target policy, PULSE QA, canonical RT/50% SOC interval
  target table, and first grouped scalar PULSE resistance baseline are
  implemented and run.
- Milestone 0.7.1 PULSE alignment-threshold sensitivity, direction-specific
  target extraction, missing canonical endpoint reports, and scalar resistance
  baseline sensitivity runs are implemented and run.
- Milestone 0.7.2 PULSE target robustness is implemented and run across
  `delta_pulse_1s_resistance`, `pulse_1s_resistance_k1`,
  `delta_pulse_10ms_resistance`, and `pulse_10ms_resistance_k1`.
- Milestone 0.8 capacity-PULSE coupling diagnostics are implemented and run:
  capacity residuals are joined to PULSE growth, and HGB-50 capacity baselines
  are rerun with prior PULSE state only.
- Milestone 0.8.1 coupling robustness diagnostics are implemented and run for
  canonical `L2_hist_gradient_boosting + F4_state_log_age_scalar` capacity
  predictions. The association survives interval- and condition-level
  aggregation, but remains explanatory and does not authorize a capacity+PULSE
  predictive claim.
- Milestone 0.9 prior-PULSE predictive comparison is implemented and run. It
  supports a narrow `capacity_Ah_k1` level-prediction claim for selected OOD
  splits, while `delta_capacity_Ah` remains a negative guardrail.
- Milestone 0.9.1 strongest non-PULSE comparison is implemented and run. It
  does not support the stronger claim that prior PULSE beats the best supplied
  non-PULSE HGB baseline.
- Milestone 1.0 evidence synthesis is now the active workstream. Its purpose is
  to lock supported, partially supported, not-supported, gated, and blocked
  claims before any EIS or new modeling path is opened.
- Milestone 1.0.1 is the active paper-artifact QA workstream. It does not add
  models or features; it prepares the synthesis artifacts for manuscript
  drafting.
- Milestone 1.1 is now the active paper-first workstream. It creates manuscript
  draft files only and keeps all new modeling, EIS modeling, feature
  engineering, CBAT, neural/sequence models, policy ranking, and broad
  multimodal claims blocked.
- Experiment notes are tracked under `docs/experiments/`.

## Git And Artifact Hygiene

Large data products and local tool artifacts remain ignored and are not tracked:

- `data/raw/**`
- `data/interim/**`
- `data/processed/**`
- generated Parquet outputs under `data/splits/`
- generated Parquet outputs under `reports/audit/`
- `.antigravitycli/`
- local CodeGraph databases, Python caches, Ruff/Pytest caches, and `.venv/`

Latest cleanup note:

- `docs/experiments/2026-05-22_repo_cleanup.md`
- Removed disposable Python, Pytest, Ruff, and empty `.antigravitycli/` local
  artifacts.
- Preserved `.venv/`, `.codegraph/`, raw/interim/processed data products, split
  Parquets, and generated audit Parquets because they are ignored local
  reproducibility or development artifacts.

Small audit sidecars that are referenced by documentation are tracked:

- `reports/audit/interval_qa_report.json`
- `reports/audit/interval_subset_report.json`
- `reports/audit/log_age_monotonicity_summary.csv`
- `reports/audit/split_registry_report.json`
- `reports/audit/stress_feature_qa_report.json`

The large Parquet outputs remain local generated artifacts:

| Artifact | Rows | Tracking |
|---|---:|---|
| `data/interim/modality_table_log_age.parquet` | 904,977,105 | ignored |
| `reports/audit/log_age_monotonicity_violations.parquet` | 7,071 | ignored |
| `data/interim/interval_table.parquet` | 3,827 | ignored |
| `data/splits/split_registry_v1.parquet` | 228 | ignored |
| `data/splits/interval_subset_registry_v1.parquet` | 3,827 | ignored |
| `data/interim/interval_stress_features_v1.parquet` | 3,827 | ignored |
| `data/interim/interval_stress_features_v1_1.parquet` | 3,827 | ignored |
| `reports/audit/raw_log_archive_inventory.parquet` | 541 | ignored |

Milestone 0.5 generated predictions are also ignored by default:

- `data/processed/capacity_baseline_predictions.parquet`
- `data/processed/capacity_l0_smoke_predictions.parquet`
- `data/processed/capacity_l0_l3_predictions.parquet`
- `data/processed/capacity_l1_scaled_predictions.parquet`
- `data/processed/capacity_hgb50_focused_predictions.parquet`
- `data/processed/capacity_stress_features_hgb50_predictions.parquet`
- `data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet`

Milestone 0.5 small report artifacts under `reports/baselines/` are trackable:

- baseline metrics JSON
- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- plot-ready CSV summaries

## Gate Status

### Gate 1

Gate 1 remains **GO FOR DATA PRODUCTS**.

Result-package coverage is complete for the 228-cell cohort:

- CFG: complete.
- EOC: complete.
- EIS: complete, but valid-frequency audit is still pending before EIS claims.
- PULSE: complete, but pulse provenance/alignment hardening remains a known
  issue.

BagIt validation for the result package passed.

### Gate 2

Gate 2 ingestion products exist for:

- `cell_condition_table`
- `checkup_event_table`
- `modality_table_eis`
- `modality_table_pulse`
- `modality_table_log_age`
- `split_registry_v1`
- `interval_table`

LOG_AGE ingestion evidence:

- Source archive: `cell_log_age_ultracompr.7z`
- Cohort rows: `904,977,105`
- Cohort cells: `228`
- Auxiliary LOG_AGE CSV records excluded: `48`
- Final Parquet row groups: `257,311`

Strict LOG_AGE QA still reports `7,107` timestamp/EFC monotonicity decreases.
That strict QA failure is preserved as an evidence signal. Milestone 0.4 defines
how those decreases are handled for baseline subset construction.

### Gate 2b

Gate 2b is complete:

- `reports/audit/log_age_monotonicity_violations.parquet` contains `7,071`
  detailed default-tolerance violations.
- `reports/audit/log_age_monotonicity_summary.csv` has `463` lines.
- Summary rows show the observed detailed violations are EFC decreases, with
  zero timestamp decreases in the default-tolerance report.
- Worst detailed EFC drops are approximately `0.0002` EFC.
- `reports/audit/interval_qa_report.json` passes.
- `reports/audit/split_registry_report.json` passes.
- `reports/audit/raw_log_archive_inventory.parquet` inventories raw LOG archive
  members without parsing the full raw LOG corpus.

Interval QA key facts:

- Interval rows: `3,827`
- Expected interval count: `3,827`
- Check-up event rows: `4,055`
- Cells with check-ups: `228`
- LOG_AGE availability fraction: `1.0`
- Intervals with zero LOG_AGE rows: `0`
- Intervals with monotonicity violations: `1,054`
- Non-cohort cells: `0`
- Masked diagnostic rows:
  - `cap_aged_est_Ah`: `4,577`
  - `R0_mOhm`: `4,577`
  - `R1_mOhm`: `4,577`

### Milestone 0.4

Milestone 0.4 data products are implemented:

- Policy: `docs/LOG_AGE_MONOTONICITY_POLICY.md`
- CLI: `mbp split interval-subsets`
- Registry: `data/splits/interval_subset_registry_v1.parquet`
- Report: `reports/audit/interval_subset_report.json`

Interval subset policy counts:

| Subset or exclusion | Count |
|---|---:|
| Full interval table | 3,827 |
| `baseline_clean_strict` | 2,773 |
| `baseline_clean_tolerant` | 3,827 |
| `sensitivity_flagged_monotonicity` | 1,054 |
| `small_efc_jitter` | 1,054 |
| Excluded due to timestamp drop | 0 |
| Excluded due to large EFC drop | 0 |
| Excluded due to missing LOG_AGE | 0 |
| Excluded due to duration error | 0 |

The tolerant subset keeps tiny EFC-only LOG_AGE jitter at or below `0.00025`
EFC. The strict subset excludes all monotonicity-flagged intervals and should be
used as the mandatory sensitivity subset for first baselines.

Split-registry audit key facts after the voltage-window fix:

- Rows: `228`
- Parameter-set triplets remain grouped.
- Condition folds are non-empty.
- Hot temperature holdout uses `40 C`.
- High C-rate holdout includes `5/3 C`.
- Profile holdout contains profile conditions.
- Voltage-window holdout is non-empty:
  - fold `1`: `84` full-window `approx_0_100` cells
  - fold `2`: `96` reduced-window `approx_10_100` / `approx_10_90` cells
  - fold `3`: `48` calendar idle-SOC cells

The legacy `soc_window_holdout_fold` remains present for compatibility but is
now populated from corrected voltage-window semantics. New work should prefer
`voltage_window_holdout_fold`.

### Milestone 0.5

Milestone 0.5 baseline tooling is implemented:

- CLI: `mbp baseline run-capacity`
- Runner: `mbp.baselines.capacity`
- Prediction schema: `BASELINE_PREDICTION_SCHEMA`
- Default primary subset: `baseline_clean_tolerant`
- Mandatory sensitivity scope: exclude
  `sensitivity_flagged_monotonicity == true`
- Targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- Split views:
  - `condition_fold`
  - `temperature_holdout_fold`
  - `c_rate_holdout_fold`
  - `profile_holdout_fold`
  - `voltage_window_holdout_fold`

Implemented model levels:

- `L0_persistence`
- `L1_ridge`
- `L2_hist_gradient_boosting`
- `L3_quantile_hist_gradient_boosting`

`L0_persistence` is dependency-free. L1-L3 require the optional baseline extra
(`uv sync --extra baseline`). The current local `.venv` was restored with
`uv sync --extra dev --extra baseline`, so both validation tooling and baseline
dependencies are available in this working environment.

Implemented feature groups:

- `F0_time_only`
- `F1_state_time`
- `F2_state_exposure`
- `F3_state_nominal`
- `F4_state_log_age_scalar`

Inserted LOG_AGE diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) are not
eligible baseline features. `F0_time_only` remains a deliberately weak sanity
feature set; learned non-persistence state-aware feature groups include
`capacity_Ah_k`.

Milestone 0.5 report rendering emits:

- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`

Completed Milestone 0.5 experiment artifacts:

- `docs/experiments/2026-05-22_capacity_baseline_ladder.md`
- `reports/baselines/capacity_l0_smoke_report.json`
- `reports/baselines/capacity_l0_smoke/leaderboard.csv`
- `reports/baselines/capacity_l0_smoke/baseline_summary.md`
- `reports/baselines/capacity_l0_smoke/evaluation_cards/*.json`
- `reports/baselines/capacity_l0_smoke/plots/*.csv`
- `reports/baselines/capacity_l0_l3_report.json`
- `reports/baselines/capacity_l0_l3/leaderboard.csv`
- `reports/baselines/capacity_l0_l3/baseline_summary.md`
- `reports/baselines/capacity_l0_l3/evaluation_cards/*.json`
- `reports/baselines/capacity_l0_l3/plots/*.csv`
- `reports/baselines/capacity_l1_scaled_report.json`
- `reports/baselines/capacity_l1_scaled/leaderboard.csv`
- `reports/baselines/capacity_l1_scaled/baseline_summary.md`
- `reports/baselines/capacity_l1_scaled/evaluation_cards/*.json`
- `reports/baselines/capacity_l1_scaled/plots/*.csv`
- `reports/baselines/capacity_hgb50_focused_report.json`
- `reports/baselines/capacity_hgb50_focused/leaderboard.csv`
- `reports/baselines/capacity_hgb50_focused/baseline_summary.md`
- `reports/baselines/capacity_hgb50_focused/evaluation_cards/*.json`
- `reports/baselines/capacity_hgb50_focused/plots/*.csv`

The L0 smoke report produced `48` metric rows on the real interval table. It
confirmed `3,827` tolerant-clean rows, `2,773` strict-clean rows, and `1,054`
monotonicity-flagged sensitivity intervals.

The bounded L0-L3 report produced `768` metric rows, `320` leaderboard rows,
and `160` evaluation cards. It used `hgb_max_iter=5`, so it is a valid first
full-ladder artifact but not a final tuned gradient-boosting run.

Primary-run baseline highlights:

- Best `capacity_Ah_k1` condition-mean MAE: `0.078735`, from `L1_ridge` with
  `F2_state_exposure` on `profile_holdout_fold`.
- Best `delta_capacity_Ah` condition-mean MAE: `0.069939`, from
  `L2_hist_gradient_boosting` with `F1_state_time` on `profile_holdout_fold`.
- Hardest split by best available condition-mean MAE:
  `c_rate_holdout_fold` at `0.175406`.
- Strict-vs-tolerant sensitivity was small on average: mean
  primary-minus-sensitivity condition-mean MAE was approximately `-0.000087`.

### Milestone 0.5b

Milestone 0.5b diagnostics and robustness artifacts are implemented:

- CLI: `mbp baseline diagnose-capacity`
- Optional reference comparison: `--reference-report`
- Diagnostics memo: `baseline_diagnostics.md`
- C-rate analysis memo: `c_rate_holdout_error_analysis.md`
- Claim-readiness memo: `claim_readiness.md`
- Diagnostic CSVs:
  - `plots/feature_gain_by_split.csv`
  - `plots/best_by_target_split.csv`
  - `plots/c_rate_holdout_errors.csv`
  - `plots/c_rate_holdout_by_condition.csv`
  - `plots/c_rate_grouped_summaries.csv`

`L1_ridge` now uses train-fold numeric standardization. Reports record
`numeric_standardization = train_fold_mean_std` and
`numeric_standardization_applies_to = ["L1_ridge"]`.

Quantile diagnostics are implemented for `L3_quantile_hist_gradient_boosting`:

- `q10_q90_interval_coverage`
- `q10_q90_interval_width_mean`
- `pinball_loss_q10`
- `pinball_loss_q50`
- `pinball_loss_q90`

Scaled Ridge rerun:

- Report: `reports/baselines/capacity_l1_scaled_report.json`
- Metric rows: `288`
- Best `capacity_Ah_k1`: `L1_ridge` with `F2_state_exposure` on
  `profile_holdout_fold`, condition-mean MAE `0.077580`.
- Scaling modestly improves several Ridge rows but does not resolve C-rate
  holdout difficulty.

Focused HGB-50 robustness rerun:

- Report: `reports/baselines/capacity_hgb50_focused_report.json`
- Metric rows: `384`
- `hgb_max_iter`: `50`
- Best `capacity_Ah_k1`: `L2_hist_gradient_boosting` with
  `F4_state_log_age_scalar` on `condition_fold`, condition-mean MAE `0.053927`.
- Best `delta_capacity_Ah`: `L2_hist_gradient_boosting` with
  `F4_state_log_age_scalar` on `condition_fold`, condition-mean MAE `0.044645`.
- Best C-rate `delta_capacity_Ah`: `0.101133`, from
  `L2_hist_gradient_boosting` with `F4_state_log_age_scalar`.
- Mean q10-q90 coverage for HGB-50 quantile rows: approximately `0.664674`.

Milestone 0.5b interpretation:

- C-rate holdout remains the hardest generalization split.
- Ridge remains sensitive to feature scaling and LOG_AGE scalar features are not
  a stable Ridge win.
- HGB-50 suggests LOG_AGE scalar summaries can help nonlinear baselines, so the
  `hgb_max_iter=5` run should be treated as a bounded smoke artifact, not as a
  final HGB conclusion.
- Nominal protocol features remain consistently useful.

### Milestone 0.5c

Milestone 0.5c synthesis artifacts are implemented:

- `docs/experiments/2026-05-22_capacity_baseline_synthesis.md`
- `reports/baselines/capacity_hgb50_focused/claim_readiness.md`
- `reports/baselines/capacity_hgb50_focused/plots/c_rate_grouped_summaries.csv`

Focused HGB-50 diagnostics were regenerated with
`--reference-report reports/baselines/capacity_l0_l3_report.json`, so the best
row table and C-rate condition table now report L0 persistence comparisons
instead of `NA`.

Milestone 0.5c key findings:

- HGB-50 improves over L0 persistence across all target/split best rows in the
  focused report.
- Best C-rate condition-mean MAE remains higher than other splits:
  `0.125186` for `capacity_Ah_k1` and `0.101133` for `delta_capacity_Ah`.
- C-rate difficulty is strongest around cold/cool high-C-rate conditions:
  grouped mean best error is `0.154004` at `10 C` and `0.132982` at `0 C`,
  versus `0.068380` at `25 C`.
- Voltage-window grouping suggests `approx_0_100` and `approx_10_100` remain
  harder than `approx_10_90` in the current C-rate diagnostic.
- Primary HGB-50 quantile q10-q90 coverage is approximately `0.678207`, below
  nominal 0.8, so no uncertainty-calibration claim is authorized.

Milestone 0.5c decision:

- Do not expand to PULSE, EIS, sequence modeling, neural modeling, policy
  ranking, or CBAT yet.
- The recommended next milestone is LOG_AGE-derived scalar stress-feature
  engineering focused on C-rate generalization.

### Milestone 0.6

Milestone 0.6 stress-feature tooling is implemented:

- CLI: `mbp features build-stress`
- CLI: `mbp features stress-qa`
- CLI: `mbp baseline diagnose-stress-features`
- Sidecar schema: `INTERVAL_STRESS_FEATURES_SCHEMA`
- Sidecar table: `data/interim/interval_stress_features_v1.parquet` (`ignored`)
- QA report: `reports/audit/stress_feature_qa_report.json`
- Baseline join option: `mbp baseline run-capacity --stress-features ...`
- Feature groups:
  - `F5_log_age_histograms`
  - `F6_coupled_stress`
  - `F7_c_rate_focused`

Stress-feature QA passed:

- Rows: `3,827`
- Unique cells: `228`
- Unique parameter sets: `76`
- Intervals missing stress features: `0`
- Dwell-bin duration consistency failures: `0`
- Negative nonnegative-feature counts: `0`
- Current-sign policy: `positive_current_charge_provisional_abs_current_primary`
- Sign-dependent features remain provisional because the current sign convention
  is not yet independently confirmed.

Target-derived diagnostic rates are excluded from F5-F7 predictive feature
groups:

- `delta_capacity_per_day`
- `delta_capacity_per_efc`
- `delta_capacity_per_Ah_throughput`

Focused stress-feature HGB-50 run:

- Report: `reports/baselines/capacity_stress_features_hgb50_report.json`
- Metric rows: `440`
- `hgb_max_iter`: `50`
- Feature groups: `F3`, `F4`, `F5`, `F6`, `F7`
- Split views: C-rate, condition, temperature, voltage-window

Milestone 0.6 success-criterion result:

| Target | HGB-50 F4 baseline | Best non-target-derived stress row | Gain | Status |
|---|---:|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.124656` (`F6_coupled_stress`) | `0.000530` | marginal pass |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.110260` (`F5_log_age_histograms`) | `-0.009128` | fail |

Stress features did not materially degrade condition-fold or
temperature-holdout performance, but the C-rate success criterion is only
partially met. The result does **not** support a broad claim that stress
features improve C-rate generalization yet.

Milestone 0.6 decision:

- Keep PULSE/EIS/CBAT blocked.
- Do not claim stress-feature improvement from v1.
- Review stress-feature formulation, current-sign convention, and event
  segmentation before expanding scope.

### Milestone 0.6.1

Milestone 0.6.1 stress-feature hardening is implemented, covered by synthetic
tests, and run on real data. The hardening keeps the scope capacity-only and
scalar-feature only.

Implemented hardening:

- CLI: `mbp features current-sign-audit`
- Stress-feature builder now emits schema version
  `gate6.interval_stress_features.v1_1`.
- Dwell features are timestamp-weighted from consecutive LOG_AGE timestamps,
  not count-weighted by row count.
- Gap and coverage fields are added:
  - `stress_observed_duration_h`
  - `stress_coverage_fraction`
  - `median_log_age_dt_s`
  - `max_log_age_gap_s`
  - `log_age_gap_count_gt_60s`
  - `log_age_gap_count_gt_300s`
- Event-segmented scalar features are added for charge, discharge, rest,
  high-current, cold/high-current, high-voltage/high-current, and
  high-SOC/high-current durations.
- New feature groups are defined:
  - `F8_timestamp_weighted_stress`
  - `F9_event_segmented_stress`
  - `F10_c_rate_v1_1`

Real-data v1.1 artifacts:

- Current-sign audit: `reports/audit/current_sign_audit_report.json`
- QA report: `reports/audit/stress_feature_v1_1_qa_report.json`
- Baseline report:
  `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
- Diagnostics:
  `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

Current-sign audit result:

- Row groups sampled evenly across LOG_AGE: `5,000`
- Positive-current evidence rows: `5,516,237`
- Negative-current evidence rows: `5,909,947`
- Convention: `positive_current_charge`
- Confidence: `high`

Stress-feature v1.1 QA result:

- Rows: `3,827`
- Unique cells: `228`
- Unique parameter sets: `76`
- Missing interval keys: `0`
- Dwell-bin failures against `stress_observed_duration_h`: `0`
- Current sign policy in sidecar: `positive_current_charge_confirmed`

Milestone 0.6.1 success-criterion result:

| Target | F4 HGB-50 baseline | v1 best stress row | v1.1 best stress row | v1.1 gain vs F4 | Status |
|---|---:|---:|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.124656` | `0.120605` (`F5_log_age_histograms`) | `0.004581` | improved but marginal |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.110260` | `0.102516` (`F8_timestamp_weighted_stress`) | `-0.001383` | fail |

Decision:

- Do not claim broad stress-feature C-rate improvement from v1.1.
- Keep PULSE/EIS/CBAT blocked.
- Treat v1.1 as a useful hardening result: current sign is now evidenced,
  timestamp-weighted dwell repaired most of the v1 delta-capacity degradation,
  but it still does not beat F4 on the main delta target.

### Milestone 0.6.2

Milestone 0.6.2 target-consistency and C-rate failure diagnostics are
implemented and run on the v1.1 stress-feature report. No new model training was
performed.

Implemented command:

- CLI: `mbp baseline diagnose-target-consistency`

Real-data outputs:

- `reports/baselines/capacity_stress_features_v1_1_hgb50/target_consistency_diagnostics.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/c_rate_residual_analysis.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_ablation_summary.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/direct_vs_derived_target_metrics.csv`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_parameter_set.csv`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`

Target-consistency finding:

| Target | C-rate rows | Derived path better by MAE | Derived path better by condition mean MAE |
|---|---:|---:|---:|
| `capacity_Ah_k1` | `14` | `10` | `10` |
| `delta_capacity_Ah` | `14` | `4` | `4` |

Best C-rate target paths by condition-mean MAE:

| Target interpreted | Best path | Model / feature group | Condition mean MAE |
|---|---|---|---:|
| `capacity_Ah_k1` | derived from direct delta | `L2_hist_gradient_boosting` / `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_Ah` | direct delta | `L2_hist_gradient_boosting` / `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_Ah` | derived from direct capacity | `L2_hist_gradient_boosting` / `F5_log_age_histograms` | `0.120605` |

Decision:

- Keep direct `delta_capacity_Ah` as the primary C-rate delta target.
- Do not switch to derived delta from capacity predictions.
- Report derived capacity-from-delta as a diagnostic because it can outperform
  direct capacity on C-rate.
- Keep PULSE/EIS/CBAT blocked until the C-rate delta failure mode is understood.

### Milestone 0.6.3

Milestone 0.6.3 tests one final narrow LOG_AGE-only C-rate delta pass before
changing evidence streams. It adds normalized delta-rate target modes,
train-fold residual/bias correction diagnostics, and compact cold/current
feature groups F11-F13.

Implemented changes:

- Target modes:
  - `delta_capacity_per_day_target`
  - `delta_capacity_per_efc_target`
- Train-fold-only residual correction via `mbp baseline run-capacity
  --bias-correction`.
- Narrow feature groups:
  - `F11_minimal_cold_current`
  - `F12_voltage_cold_current_interactions`
  - `F13_sparse_c_rate_context`

Real-data outputs:

- `reports/baselines/capacity_delta_rate_targets_hgb50_report.json`
- `reports/baselines/capacity_delta_rate_targets_hgb50/plots/rate_target_vs_direct_delta.csv`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_c_rate_bias_corrected_report.json`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/bias_correction_by_split.csv`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`

C-rate `delta_capacity_Ah` result:

| Approach | Best C-rate condition-mean MAE | Beats `0.101133` F4 threshold |
|---|---:|---|
| Direct F4 baseline | `0.101133` | reference |
| Normalized rate targets | `0.121271` best rate target | no |
| Narrow F11-F13 groups | `0.147452` best narrow group | no |
| Train-fold bias correction | effectively unchanged from direct F4 | no |

Decision:

- Keep direct `delta_capacity_Ah` as the primary delta target.
- Do not use normalized rate targets as the next primary target path.
- Do not promote F11-F13 narrow cold/current groups as evidence.
- Treat train-fold residual correction as neutral diagnostics, not a headline
  model.
- Stop broad LOG_AGE scalar stress-feature expansion unless a future review
  identifies a concrete bug. The next recommended evidence stream is PULSE
  QA/baseline work, while EIS/PULSE supervised claims remain blocked until that
  milestone is explicitly opened.

### Milestone 0.7

Milestone 0.7 opens PULSE as a QA-first resistance endpoint. It does not
authorize EIS, sequence/neural models, policy ranking, CBAT, or capacity+PULSE
multimodal claims.

Implemented artifacts:

- Policy: `docs/PULSE_TARGET_POLICY.md`
- CLI: `mbp pulse qa`
- CLI: `mbp pulse build-targets`
- CLI: `mbp baseline run-pulse`
- QA report: `reports/audit/pulse_qa_report.json`
- Alignment report: `reports/audit/pulse_alignment_report.json`
- Coverage table: `reports/audit/pulse_target_coverage.csv`
- Target table: `data/interim/pulse_target_table.parquet` (ignored generated data)
- Baseline report: `reports/baselines/pulse_resistance_l0_l3_report.json`
- Diagnostics: `reports/baselines/pulse_resistance_l0_l3/pulse_diagnostics.md`
- Experiment note: `docs/experiments/2026-05-23_pulse_qa_resistance_baseline.md`

PULSE QA findings:

| Field | Value |
|---|---:|
| PULSE summary rows | `39,365` |
| Unique cells | `228` |
| Canonical RT/50% cell-checkups available | `3,980` |
| Canonical RT/50% cell-checkups missing | `75` |
| Duplicate canonical cell-checkups | `0` |
| Large alignment-delta rows > 1 day | `5,060` |

Canonical target-table findings:

| Field | Finite intervals |
|---|---:|
| `pulse_1s_resistance_k` | `3,826` |
| `pulse_1s_resistance_k1` | `3,752` |
| `delta_pulse_1s_resistance` | `3,751` |
| `delta_pulse_10ms_resistance` | `3,751` |

First PULSE baseline result for `delta_pulse_1s_resistance`:

| Split | Best model | Feature group | Condition-mean MAE |
|---|---|---|---:|
| `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | `0.000960407` |
| `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | `0.00109610` |
| `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | `0.00185842` |
| `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | `0.000953406` |
| `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | `0.00117733` |

Decision:

- PULSE RT/50% target coverage is good enough for first baseline diagnostics,
  but missing canonical endpoints and large alignment deltas must remain visible
  in reports.
- The first PULSE resistance baseline is diagnostic only; no scientific PULSE
  claim or capacity+PULSE multimodal claim is authorized yet.
- Next work should harden PULSE alignment/target coverage interpretation before
  considering broader PULSE target sets.

### Milestone 0.7.1

Milestone 0.7.1 hardens the canonical PULSE target before any resistance claim.
It does not authorize EIS, sequence/neural models, policy ranking, CBAT,
capacity+PULSE multimodal claims, or PULSE claims beyond scalar resistance
baselines.

Implemented artifacts:

- CLI: `mbp pulse alignment-sensitivity`
- CLI: `mbp pulse missingness`
- CLI option: `mbp pulse build-targets --direction mean|charge|discharge`
- CLI option: `mbp baseline run-pulse --max-alignment-delta-s`
- Alignment sensitivity report:
  `reports/audit/pulse_alignment_sensitivity_report.json`
- Alignment sensitivity coverage:
  `reports/audit/pulse_alignment_sensitivity_coverage.csv`
- Missing endpoint reports:
  `reports/audit/pulse_missing_canonical_targets.csv`,
  `reports/audit/pulse_missingness_by_condition.csv`, and
  `reports/audit/pulse_missingness_by_split.csv`
- Direction-specific target tables:
  `data/interim/pulse_target_table_mean.parquet`,
  `data/interim/pulse_target_table_charge.parquet`, and
  `data/interim/pulse_target_table_discharge.parquet` (ignored generated data)
- Alignment-threshold baseline reports:
  `reports/baselines/pulse_resistance_alignment_24h_report.json` and
  `reports/baselines/pulse_resistance_alignment_36h_report.json`
- Direction sensitivity reports:
  `reports/baselines/pulse_resistance_direction_mean_report.json`,
  `reports/baselines/pulse_resistance_direction_charge_report.json`, and
  `reports/baselines/pulse_resistance_direction_discharge_report.json`
- Combined summaries:
  `reports/baselines/pulse_resistance_alignment_sensitivity/baseline_summary.md`
  and
  `reports/baselines/pulse_resistance_l0_l3/pulse_resistance_direction_comparison.md`

Canonical RT/50 alignment-threshold coverage:

| Threshold | Retained intervals | Missing intervals | Retained cells | C-rate rows | Profile rows |
|---|---:|---:|---:|---:|---:|
| `<=6h` | `3,131` | `696` | `220` | `90` | `605` |
| `<=12h` | `3,529` | `298` | `225` | `109` | `697` |
| `<=24h` | `3,748` | `79` | `228` | `143` | `733` |
| `<=36h` | `3,751` | `76` | `228` | `143` | `733` |
| `all` | `3,751` | `76` | `228` | `143` | `733` |

Alignment-threshold baseline sensitivity:

| Threshold | Split | Best feature group | Condition-mean MAE |
|---|---|---|---:|
| `all` | `condition_fold` | `P5_stress_v1_1` | `0.000960407` |
| `all` | `c_rate_holdout_fold` | `P3_state_nominal` | `0.00185842` |
| `<=24h` | `condition_fold` | `P5_stress_v1_1` | `0.000952007` |
| `<=24h` | `c_rate_holdout_fold` | `P3_state_nominal` | `0.00194971` |
| `<=36h` | `condition_fold` | `P5_stress_v1_1` | `0.000960407` |
| `<=36h` | `c_rate_holdout_fold` | `P3_state_nominal` | `0.00185842` |

Direction sensitivity:

- `mean` remains the canonical PULSE target direction handling.
- `charge` produced the same scalar baseline rows as `mean` for the current
  canonical RT/50 target table.
- `discharge` produced no finite adjacent RT/50 interval deltas and now emits
  an explicit warning report: `no_finite_target_rows_for_selected_configuration`.

Missing canonical endpoints:

- Missing endpoint rows: `76`
- Missing rows in C-rate holdout: `14`
- Missing rows in profile holdout: `19`
- Missingness spans `34` parameter-set condition groups and remains a reporting
  limitation rather than a silent exclusion.

Decision:

- Alignment filtering at `<=24h` changes the C-rate condition-mean MAE slightly
  and keeps all parameter sets represented; `<=36h` is identical to all rows for
  the current finite target set.
- Direction-specific discharge is not usable as a current canonical baseline
  target because adjacent finite RT/50 discharge deltas are absent.
- The canonical `mean` target remains acceptable for scalar resistance-baseline
  diagnostics, but no PULSE scientific claim or capacity+PULSE multimodal claim
  is authorized.

### Milestone 0.7.2

Milestone 0.7.2 finalizes scalar PULSE target robustness before any
capacity+PULSE coupling work. It does not authorize EIS, sequence/neural
models, policy ranking, CBAT, capacity+PULSE multimodal claims, or PULSE claims
beyond scalar resistance baselines.

Implemented artifacts:

- Target robustness report:
  `reports/baselines/pulse_resistance_target_robustness_report.json`
- Target robustness directory:
  `reports/baselines/pulse_resistance_target_robustness/`
- Claim-readiness memo:
  `reports/baselines/pulse_resistance_l0_l3/pulse_claim_readiness.md`
- Alignment robustness memo:
  `reports/baselines/pulse_resistance_alignment_robustness.md`
- Direction policy summary:
  `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`
- Missingness interpretation:
  `reports/audit/pulse_missingness_interpretation.md`
- Decision memo:
  `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`

Best target-robustness rows:

| Target | C-rate best MAE | Condition-fold best MAE | Interpretation |
|---|---:|---:|---|
| `delta_pulse_1s_resistance` | `0.00185842` | `0.000960407` | canonical transition target |
| `delta_pulse_10ms_resistance` | `0.00180642` | `0.000910676` | viable secondary diagnostic |
| `pulse_1s_resistance_k1` | `0.00189616` | `0.00104973` | state-tracking target |
| `pulse_10ms_resistance_k1` | `0.00179792` | `0.00105917` | state-tracking target |

Decision:

- `delta_pulse_1s_resistance` remains the canonical first PULSE transition
  target.
- `delta_pulse_10ms_resistance` behaves similarly and is viable as a secondary
  diagnostic target.
- k1 resistance targets should be interpreted as state-tracking targets, not
  direct transition prediction.
- Current RT/50 `mean` direction handling is effectively equivalent to
  `charge`; discharge adjacent interval deltas are unavailable.
- Canonical RT/50 mean PULSE is robust enough for scalar resistance-baseline
  diagnostics. A broader PULSE scientific claim and capacity+PULSE multimodal
  modeling remain blocked until explicitly opened.

### Milestone 0.8

Milestone 0.8 tests whether scalar canonical PULSE signals explain capacity
baseline failures. It is not architecture work and does not authorize
capacity+PULSE multimodal claims.

Implemented artifacts:

- Coupling table:
  `data/interim/capacity_pulse_coupling_table.parquet` (ignored generated data)
- Coupling diagnostics:
  `reports/coupling/pulse_capacity/pulse_capacity_correlation.md`
- Coupling plot tables under `reports/coupling/pulse_capacity/plots/`
- Prior-PULSE capacity report:
  `reports/baselines/capacity_with_prior_pulse_hgb50_report.json`
- Prior-PULSE capacity diagnostics:
  `reports/baselines/capacity_with_prior_pulse_hgb50/pulse_feature_gain.md`
- Decision memo:
  `docs/experiments/2026-05-23_capacity_pulse_coupling_diagnostics.md`

Capacity residual/PULSE-growth correlations from the focused HGB-50 capacity
report:

| Scope | Target | Residual | Pearson | Spearman |
|---|---|---|---:|---:|
| all | `capacity_Ah_k1` | absolute residual | `0.559997` | `0.236657` |
| all | `delta_capacity_Ah` | absolute residual | `0.604807` | `0.304910` |
| C-rate | `capacity_Ah_k1` | absolute residual | `0.894547` | `0.664034` |
| C-rate | `delta_capacity_Ah` | absolute residual | `0.822463` | `0.639033` |
| cold C-rate | `capacity_Ah_k1` | absolute residual | `0.877023` | `0.824406` |
| cold C-rate | `delta_capacity_Ah` | absolute residual | `0.769408` | `0.723490` |

Best prior-PULSE capacity gains versus F4 on the PULSE-covered interval
population:

| Target | Split | Best prior-PULSE group | Gain vs F4 |
|---|---|---|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `0.00669208` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `-0.00574230` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `0.00509620` |
| `delta_capacity_Ah` | condition | `C_P3_stress_pulse` | `0.00249507` |

Decision:

- PULSE growth is strongly associated with capacity residual magnitude,
  especially in C-rate and cold C-rate views.
- Prior PULSE state improves `capacity_Ah_k1` on C-rate, temperature, profile,
  and most other views.
- Prior PULSE state does not solve the C-rate `delta_capacity_Ah` failure; the
  best C-rate delta prior-PULSE row is worse than F4.
- The result supports PULSE as an explanatory scalar diagnostic endpoint, but
  not yet a capacity+PULSE predictive claim or multimodal architecture.

### Milestone 0.8.1

Milestone 0.8.1 checks whether the 0.8 prediction-row coupling signal survives
canonical-model filtering, interval-level aggregation, condition-level
aggregation, parameter-set bootstrap, and simple confound-control
residualization.

Implemented artifacts:

- CLI: `mbp coupling pulse-capacity-robustness`
- Capacity target robustness directory:
  `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/`
- Delta target robustness directory:
  `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah/`
- C-rate split robustness directories:
  `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate/` and
  `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate/`
- Decision memo:
  `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md`

Canonical all-split interval/condition results for
`L2_hist_gradient_boosting + F4_state_log_age_scalar`:

| Target | Level | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | interval abs residual | 3,751 | `0.593280` | `0.304567` |
| `capacity_Ah_k1` | condition abs residual | 76 | `0.903834` | `0.905345` |
| `delta_capacity_Ah` | interval abs residual | 3,751 | `0.485245` | `0.314490` |
| `delta_capacity_Ah` | condition abs residual | 76 | `0.779516` | `0.773069` |

Canonical C-rate-split results:

| Target | Level | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | interval abs residual | 143 | `0.857653` | `0.633959` |
| `capacity_Ah_k1` | condition abs residual | 12 | `0.956599` | `0.979021` |
| `delta_capacity_Ah` | interval abs residual | 143 | `0.647125` | `0.646779` |
| `delta_capacity_Ah` | condition abs residual | 12 | `0.903590` | `0.881119` |

Residualized diagnostic correlations after controlling for observed state and
condition metadata:

| Target | Scope | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | all intervals | 3,751 | `0.451220` | `0.251932` |
| `capacity_Ah_k1` | C-rate split | 143 | `0.838145` | `0.627044` |
| `delta_capacity_Ah` | all intervals | 3,751 | `0.330324` | `0.182004` |
| `delta_capacity_Ah` | C-rate split | 143 | `0.519771` | `0.447610` |

Decision:

- PULSE growth remains associated with capacity residual magnitude after
  canonical-model filtering and interval-level aggregation.
- The association is stronger at parameter-set condition level, especially in
  C-rate views, but the C-rate condition sample is small.
- Basic residualization weakens the all-interval association, especially for
  `delta_capacity_Ah`, but C-rate split associations remain visible.
- The result strengthens PULSE as an explanatory scalar diagnostic endpoint.
- A capacity+PULSE predictive claim remains blocked because prior PULSE did not
  solve C-rate `delta_capacity_Ah`, and this milestone is diagnostic rather than
  a predictive benchmark.

### Milestone 0.9

Milestone 0.9 compares the F4 HGB capacity baseline against prior-PULSE feature
groups on the same PULSE-covered interval population. The only allowed PULSE
capacity input is `pulse_1s_resistance_k`. Future PULSE states and PULSE deltas
remain forbidden.

Implemented artifacts:

- CLI: `mbp baseline compare-prior-pulse-capacity`
- Report directory:
  `reports/baselines/capacity_prior_pulse_predictive/`
- Paired condition gains:
  `reports/baselines/capacity_prior_pulse_predictive/paired_condition_gain.csv`
- Split-level bootstrap summary:
  `reports/baselines/capacity_prior_pulse_predictive/split_level_gain_summary.csv`
- C-rate summary:
  `reports/baselines/capacity_prior_pulse_predictive/c_rate_gain_summary.csv`
- Coverage effects:
  `reports/baselines/capacity_prior_pulse_predictive/coverage_effect_summary.csv`
- Claim readiness:
  `reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_claim_readiness.md`
- Decision memo:
  `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md`

Paired condition-level gain summary:

| Target | Split | Best prior-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | 12 | `0.00669208` | `0.000718651` | `0.00678842` | `0.0131255` | `0.666667` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | 38 | `0.00509620` | `0.00103230` | `0.00493892` | `0.00974339` | `0.605263` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | 12 | `0.0214905` | `0.0137834` | `0.0214668` | `0.0299696` | `0.916667` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | 12 | `-0.00574230` | `-0.0203466` | `-0.00552136` | `0.00835579` | `0.5` |

Coverage effect:

- Capacity-only selected rows: `3,827`
- PULSE-covered selected rows: `3,826`
- Dropped intervals from requiring prior PULSE: `1`
- PULSE-covered parameter sets: `76`
- C-rate interval coverage is unchanged for both capacity targets.

Decision:

- Prior PULSE state supports a narrow non-neural `capacity_Ah_k1`
  level-prediction claim in C-rate, temperature, and profile split diagnostics.
- Prior PULSE does not support a `delta_capacity_Ah` fade-rate claim; C-rate
  delta gain remains negative.
- Coverage loss is small and does not change parameter-set coverage.
- Broad multimodal claims, future-PULSE inputs, EIS, sequence/neural models,
  policy ranking, and CBAT remain blocked.

### Milestone 0.9.1

Milestone 0.9.1 compares prior-PULSE feature groups against the strongest
supplied non-PULSE HGB baselines on the same PULSE-covered interval population.
The non-PULSE pool used the focused HGB-50 report and the v1.1 stress-feature
HGB-50 report.

Implemented artifacts:

- CLI: `mbp baseline compare-prior-pulse-vs-best-nonpulse`
- Report directory:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/`
- Paired gains:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/paired_gain_vs_best_nonpulse.csv`
- Split-level bootstrap summary:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`
- C-rate summary:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/c_rate_gain_vs_best_nonpulse.csv`
- Claim readiness:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md`
- Decision memo:
  `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`

Paired gains versus strongest supplied non-PULSE baselines:

| Target | Split | Prior-PULSE group | Best non-PULSE group | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `F5_log_age_histograms` | `0.000392605` | `-0.00553843` | `0.000727887` | `0.00645520` | `0.5` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `F6_coupled_stress` | `-0.000753049` | `-0.00294184` | `-0.000680351` | `0.00123690` | `0.552632` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | `F1_state_time` | `-0.000697582` | `-0.00281975` | `-0.000582270` | `0.00111274` | `0.583333` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `F4_state_log_age_scalar` | `-0.00234428` | `-0.0169742` | `-0.00185231` | `0.0119867` | `0.583333` |

Decision:

- Prior PULSE still improves over F4 in Milestone 0.9, but the stronger
  “beats best supplied non-PULSE baseline” claim is not supported.
- The best non-PULSE C-rate `capacity_Ah_k1` baseline is
  `F5_log_age_histograms`; prior PULSE is only marginally better on mean gain
  and has a bootstrap interval crossing zero.
- Temperature/profile `capacity_Ah_k1` gains versus strongest non-PULSE are
  negative on average.
- `delta_capacity_Ah` remains unsupported.
- Keep only the narrow “prior PULSE improves over F4” statement. Do not claim
  prior PULSE is the best available non-neural capacity feature path.

### Milestone 1.0

Milestone 1.0 is evidence synthesis and paper-claim lock. It adds no new model
training or feature engineering. The active goal is to convert the completed
baseline sequence into paper-facing artifacts that separate supported claims
from partial, negative, gated, and blocked claims.

Implemented synthesis artifacts:

- Claim ledger: `docs/PAPER_CLAIM_LEDGER.md`
- Figure/table plan: `docs/PAPER_FIGURE_PLAN.md`
- Paper skeleton: `docs/PAPER_SKELETON.md`
- Experiment synthesis:
  `docs/experiments/2026-05-23_evidence_synthesis.md`
- Claim matrix: `reports/synthesis/claim_matrix.csv`
- Evidence matrix: `reports/synthesis/evidence_matrix.md`
- Model ladder summary: `reports/synthesis/model_ladder_summary.csv`
- Split difficulty summary: `reports/synthesis/split_difficulty_summary.csv`
- Negative-result summary: `reports/synthesis/negative_results.md`

Locked claim posture:

- LOG_AGE scalar features and stress features are partially supported, but they
  do not solve C-rate `delta_capacity_Ah`.
- C-rate holdout is the hardest capacity generalization view.
- Canonical RT/50 PULSE is ready for scalar resistance-baseline diagnostics.
- PULSE growth is supported as an explanatory diagnostic for capacity residuals,
  especially in C-rate views.
- Prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped splits, but
  it does not beat the strongest supplied non-PULSE HGB baselines and does not
  improve `delta_capacity_Ah`.
- Quantile HGB uncertainty is not calibrated.
- EIS and CBAT remain gated/blocked.

### Milestone 1.0.1

Milestone 1.0.1 is paper artifact QA and manuscript packaging. It keeps the
project documentation-only and does not authorize model training, new feature
engineering, EIS modeling, neural/sequence models, policy ranking, CBAT, or
broad multimodal claims.

Implemented paper-QA artifacts:

- Manuscript package plan: `docs/MANUSCRIPT_PACKAGE_PLAN.md`
- Source artifact checklist:
  `reports/synthesis/source_artifact_checklist.md`
- Reviewer-risk register:
  `reports/synthesis/reviewer_risk_register.md`

Consistency updates:

- Claim C01 is tightened to:
  "Current scalar LOG_AGE summaries help nonlinear models in some grouped
  views, but gains are mixed."
- `reports/synthesis/split_difficulty_summary.csv` now states that best-known
  rows are descriptive and do not override paired claim-readiness tests.
- The evidence synthesis memo now explicitly states that descriptive prior-PULSE
  best-row delta results do not authorize a fade-rate claim.

### Milestone 1.1

Milestone 1.1 is manuscript draft package v0.1. It is writing and
source-traceability work only. It does not add model training, feature
engineering, EIS modeling, neural/sequence models, policy ranking, CBAT, or
broad multimodal claims.

Implemented manuscript package:

- Package README: `manuscript/README.md`
- Manuscript outline: `manuscript/outline.md`
- Draft sections:
  - `manuscript/abstract_v0.md`
  - `manuscript/introduction_v0.md`
  - `manuscript/methods_data_products_v0.md`
  - `manuscript/methods_validation_v0.md`
  - `manuscript/results_capacity_baselines_v0.md`
  - `manuscript/results_stress_features_v0.md`
  - `manuscript/results_pulse_resistance_v0.md`
  - `manuscript/results_capacity_pulse_coupling_v0.md`
  - `manuscript/discussion_negative_results_v0.md`
  - `manuscript/limitations_v0.md`
- Figure specs: `manuscript/figures/*.md`
- Table specs: `manuscript/tables/*.md`
- Source traceability: `manuscript/source_traceability.md`
- Reviewer response prep: `manuscript/reviewer_response_prep.md`
- Experiment note:
  `docs/experiments/2026-05-23_manuscript_draft_package.md`

The manuscript package uses the Milestone 1.0/1.0.1 claim posture:

- supported: grouped validation benchmark, C-rate difficulty, RT/50 PULSE
  scalar endpoint;
- diagnostic: PULSE growth as residual explanatory signal;
- partial: mixed LOG_AGE value and prior-PULSE-over-F4 level prediction;
- not supported: stress features solving C-rate fade, prior PULSE beating
  strongest non-PULSE, prior PULSE improving `delta_capacity_Ah`, calibrated
  HGB uncertainty;
- gated/blocked: EIS, CBAT, neural/sequence models, policy ranking, and broad
  multimodal claims.

## Important Implementation Notes

The interval builder preserves result-table timestamps in the public schema, but
uses per-cell relative LOG_AGE windows internally when scanning reduced logs.
This matters because:

- `checkup_event_table.timestamp` is epoch-like result time.
- `modality_table_log_age.timestamp_s` is relative operating time.

The mismatch is covered by
`test_aligns_epoch_checkups_to_relative_log_age_time`.

The LOG_AGE monotonicity audit writes atomically:

- Details are written to a temporary Parquet path first.
- The final report is replaced only after the writer closes successfully.

This prevents a crash or timeout from leaving a corrupt final Parquet report.

The interval subset registry writes Parquet metadata for:

- schema version
- monotonicity policy version
- EFC jitter threshold
- source interval table path

## Baseline Authorization

Baseline data-product prerequisites and the first capacity baseline runner now
exist. First baseline work must use:

- primary subset: `baseline_clean_tolerant`
- mandatory sensitivity subset: exclude
  `sensitivity_flagged_monotonicity == true`
- targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- split views: condition, temperature, C-rate, profile, and corrected
  voltage-window holdouts
- no EIS, sequence models, neural models, policy ranking, CBAT architecture, or
  capacity+PULSE multimodal claims

EIS claims and PULSE scientific claims beyond scalar resistance baselines remain
blocked by their known audit issues. EIS modeling, capacity+PULSE multimodal
claims, sequence/neural models, policy ranking, and CBAT remain blocked.

## Validation

Latest validation run:

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
107 passed.
```

Milestone 1.0 adds documentation and tracked synthesis CSV/Markdown artifacts
only. No new code or generated Parquet data products are introduced by this
synthesis step.

Milestone 1.1 adds manuscript Markdown files only. No new code, model training,
feature engineering, generated Parquet data products, or prediction artifacts
are introduced by the manuscript draft package. Milestone 1.1 validation checks
are limited to Markdown/CSV consistency, claim-ID mapping, source-artifact
existence, and forbidden-wording scans.

The previous `datetime.utcnow()` deprecation warning in
`src/mbp/data/luh_blank/qa_result_data.py` has been fixed.

## Recommended Next Step

Review the **Milestone 1.1 Manuscript Draft Package v0.1**. The preferred next
branch is paper-first v0.2 drafting or figure-generation packaging, not new
modeling. If a technical stream is needed afterward, open a separately gated
EIS QA and feature-validation milestone; do not jump directly to EIS modeling,
sequence models, neural models, policy ranking, CBAT, or broad multimodal
claims.
