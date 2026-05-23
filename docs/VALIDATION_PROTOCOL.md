# Validation Protocol

Milestone 0.5/0.5b/0.5c/0.6/0.6.1/0.6.2/0.6.3 authorizes only scalar capacity baseline work on
interval features. Milestone 0.5b is review and robustness hardening. Milestone
0.5c is synthesis and stress-feature decision work. Milestone 0.6 adds
capacity-only LOG_AGE-derived scalar stress features. Milestone 0.6.1 hardens
those features with current-sign audit evidence, timestamp-weighted dwell, and
event-segmented scalar summaries. Milestone 0.6.2 audits target consistency and
C-rate failure modes without adding new modalities or model classes. Milestone
0.6.3 permits normalized delta-rate target diagnostics, train-fold residual
bias-correction diagnostics, and narrow cold/current stress feature groups.
These milestones are not modality or architecture expansions.

Milestone 0.7 opens PULSE as a separate QA-first resistance endpoint. It
authorizes PULSE QA, canonical PULSE target extraction, PULSE interval target
tables, and scalar grouped PULSE resistance baselines. Milestone 0.7.1 hardens
that endpoint with alignment-threshold sensitivity, direction-specific target
tables, canonical-target missingness reports, and scalar resistance baseline
sensitivity runs. Milestone 0.7.2 evaluates secondary PULSE targets and
claim-readiness for scalar resistance baselines. Milestone 0.8 authorizes
capacity-PULSE scalar coupling diagnostics and prior-PULSE capacity baseline
feature checks. Milestone 0.8.1 authorizes robustness checks for those coupling
diagnostics: canonical-model selection, interval-level aggregation,
condition-level aggregation, parameter-set bootstrap summaries, and simple
confound-control residualization. Milestone 0.9 authorizes only a narrow
non-neural prior-PULSE predictive baseline for `capacity_Ah_k1`, using prior
PULSE state at check-up `k` only and paired grouped comparisons. It does not
authorize EIS modeling, future PULSE state, PULSE deltas as capacity inputs,
broad capacity+PULSE multimodal claims, sequence models, neural models, policy
ranking, or CBAT. Milestone 0.9.1 compares prior-PULSE groups against the
strongest supplied non-PULSE HGB baselines before strengthening the 0.9 claim.
Milestone 1.0 is evidence synthesis and paper-claim lock. It authorizes only
documentation, claim ledgers, figure/table planning, negative-result summaries,
and source-artifact cross-checks. It does not authorize new model training, new
feature engineering, EIS modeling, broad multimodal claims, sequence models,
neural models, policy ranking, or CBAT.
Milestone 1.0.1 is paper artifact QA and manuscript packaging. It authorizes
claim wording refinement, source-artifact checklists, figure/table packaging,
manuscript outline tightening, and reviewer-risk registers. It still does not
authorize new model training, feature engineering, EIS modeling, neural models,
sequence models, policy ranking, CBAT, or broad multimodal claims.
Milestone 1.1 is manuscript draft package v0.1. It authorizes draft prose,
figure/table specifications, claim-to-section mapping, source traceability, and
reviewer-risk mitigation prose. It is still paper-first work only and does not
authorize new model training, feature engineering, EIS modeling, neural models,
sequence models, policy ranking, CBAT, or broad multimodal claims.
Milestone 1.2 is figure/table generation and manuscript v0.2 assembly. It
authorizes only generated figures/tables from existing tracked artifacts,
caption drafting, continuous manuscript assembly, source-traceability checks,
and no-overclaim checks. It still does not authorize new model training, new
feature engineering, EIS modeling, neural models, sequence models, policy
ranking, CBAT, or broad multimodal claims.
Milestone 1.3 is manuscript v0.3 polish and figure QA. It authorizes manuscript
prose polish, generated figure/table QA, source traceability hardening,
caption/table wording cleanup, and expanded no-overclaim checks across
paper-facing manuscript files. It still does not authorize new model training,
new feature engineering, EIS modeling, neural models, sequence models, policy
ranking, CBAT, or broad multimodal claims.
Milestone 1.4 is reader-facing manuscript v0.4 and publication figure pass. It
authorizes reader-facing manuscript assembly, figure/caption polish from
existing artifacts, traceability sidecar updates, and reader-facing
no-overclaim checks. It still does not authorize new model training, new
feature engineering, EIS modeling, neural models, sequence models, policy
ranking, CBAT, or broad multimodal claims.
Milestone 1.4.1 is reader-facing cleanup and check hardening. It authorizes
only removal of remaining internal scaffold language, reader-check hardening,
caption/figure wording cleanup, and no-overclaim checks. It still does not
authorize new model training, new feature engineering, EIS modeling, neural
models, sequence models, policy ranking, CBAT, or broad multimodal claims.
Milestone 2.0 is EIS QA and feature gate. It authorizes EIS coverage
diagnostics, spectrum-quality summaries, valid-frequency mask audits,
alignment-threshold sensitivity, the EIS feature policy, E0/E1/E2/E3 scalar
feature table construction, feature QA, and EIS claim-readiness reporting. It
does not authorize EIS predictive modeling, EIS embeddings, DRT features,
capacity+PULSE+EIS multimodal models, neural models, sequence models, policy
ranking, CBAT, or any EIS improvement claim.
Milestone 2.1 is EIS scalar diagnostic baselines. It authorizes EIS interval
target tables, EIS scalar target QA, non-neural scalar EIS baselines, and
prior-EIS feature groups for PULSE/capacity baselines using check-up `k` EIS
features only. It does not authorize DRT, EIS embeddings, future EIS state or
EIS deltas as capacity/PULSE inputs, neural models, sequence models, CBAT,
policy ranking, capacity+PULSE+EIS multimodal models, or broad EIS improvement
claims.
Milestone 2.1.1 hardens scalar EIS claims with strongest non-EIS comparisons,
parameter-set bootstrap intervals, alignment sensitivity, feature-completeness
sensitivity, and leakage audits. Milestone 2.2 authorizes semi-empirical
stress comparators and condition-triplet replicate uncertainty diagnostics. It
does not authorize neural models, sequence models, CBAT, DRT, EIS embeddings,
policy ranking, capacity+PULSE+EIS architecture work, or causal/mechanistic
overclaims.
Milestone 2.3 authorizes grouped capacity calibration diagnostics:
split-conformal intervals, stressor-family conformal intervals, replicate-aware
hybrid intervals, coverage/width reports, and calibration claim-readiness. It
does not authorize neural models, sequence models, CBAT, DRT, EIS embeddings,
policy ranking, capacity+PULSE+EIS architecture work, causal/mechanistic
claims, or calibrated uncertainty claims unless grouped coverage passes without
test-residual leakage.

Required split discipline:

- Primary evidence uses condition-level grouped splits.
- Replicates from the same parameter-set condition remain together for headline
  claims.
- Random row/cell splits are leakage smoke tests only and are not part of the
  Milestone 0.5 baseline report.
- LOG_AGE inserted diagnostics must remain masked for interval prediction.
- Baseline code must consume `interval_subset_registry_v1.parquet`.
- The primary capacity run uses `baseline_clean_tolerant`.
- Every baseline report must include a sensitivity run excluding
  `sensitivity_flagged_monotonicity == true`.

Required Milestone 1.0 synthesis artifacts:

- `docs/experiments/2026-05-23_evidence_synthesis.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `docs/PAPER_FIGURE_PLAN.md`
- `docs/PAPER_SKELETON.md`
- `reports/synthesis/claim_matrix.csv`
- `reports/synthesis/evidence_matrix.md`
- `reports/synthesis/model_ladder_summary.csv`
- `reports/synthesis/split_difficulty_summary.csv`
- `reports/synthesis/negative_results.md`

Required Milestone 1.0.1 paper-QA artifacts:

- `docs/MANUSCRIPT_PACKAGE_PLAN.md`
- `reports/synthesis/source_artifact_checklist.md`
- `reports/synthesis/reviewer_risk_register.md`

Required Milestone 1.1 manuscript package artifacts:

- `manuscript/README.md`
- `manuscript/outline.md`
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
- `manuscript/source_traceability.md`
- `manuscript/reviewer_response_prep.md`
- `manuscript/figures/*.md`
- `manuscript/tables/*.md`

Required Milestone 1.2 manuscript asset artifacts:

- `manuscript/manuscript_v0_2.md`
- `manuscript/figures/generated/*.svg`
- `manuscript/tables/generated/*.md`
- `manuscript/captions/figure_captions.md`
- `manuscript/captions/table_captions.md`
- `manuscript/checks/manuscript_claim_check.md`
- `manuscript/checks/figure_source_check.md`
- `docs/experiments/2026-05-23_manuscript_v0_2_assets.md`

Required Milestone 1.3 manuscript polish artifacts:

- `manuscript/manuscript_v0_3.md`
- corrected `manuscript/figures/generated/fig06_pulse_qa_coverage.svg`
- `manuscript/checks/figure_data_check.md`
- updated caption files with "what not to infer" notes
- `docs/experiments/2026-05-23_manuscript_v0_3_polish.md`

Required Milestone 1.4 reader-facing artifacts:

- `manuscript/manuscript_v0_4.md`
- `manuscript/manuscript_v0_4_traceability.md`
- `manuscript/captions/figure_captions_v0_4.md`
- `manuscript/captions/table_captions_v0_4.md`
- `manuscript/checks/manuscript_v0_4_claim_check.md`
- `manuscript/checks/manuscript_v0_4_reader_check.md`
- `manuscript/figures/generated_v0_4/*.svg`
- `docs/experiments/2026-05-23_manuscript_v0_4_reader_polish.md`

Required Milestone 1.4.1 cleanup artifacts:

- cleaned `manuscript/manuscript_v0_4.md` without `Forbidden wording:`
- updated `manuscript/manuscript_v0_4_traceability.md` with prose guardrails
- regenerated `manuscript/figures/generated_v0_4/*.svg` without internal draft
  labels
- `docs/experiments/2026-05-23_manuscript_v0_4_1_reader_cleanup.md`

Required Milestone 2.0 EIS QA artifacts:

- `docs/EIS_FEATURE_POLICY.md`
- `reports/audit/eis_qa_report.json`
- `reports/audit/eis_coverage_report.csv`
- `reports/audit/eis_alignment_report.json`
- `reports/audit/eis_alignment_sensitivity_report.json`
- `reports/audit/eis_alignment_sensitivity_coverage.csv`
- `reports/audit/eis_spectrum_quality_summary.csv`
- `reports/audit/eis_valid_frequency_report.csv`
- `data/interim/eis_feature_table_v1.parquet` (ignored generated artifact)
- `reports/audit/eis_feature_qa_report.json`
- `reports/audit/eis_claim_readiness.md`
- `docs/experiments/2026-05-23_eis_qa_feature_gate.md`

Required Milestone 2.1 EIS scalar diagnostic artifacts:

- `data/interim/eis_target_table_v1.parquet` (ignored generated artifact)
- `reports/audit/eis_target_qa_report.json`
- `reports/audit/eis_target_coverage.csv`
- `reports/baselines/eis_scalar_l0_l3_report.json`
- `reports/baselines/eis_scalar_l0_l3/leaderboard.csv`
- `reports/baselines/eis_scalar_l0_l3/baseline_summary.md`
- `reports/baselines/eis_scalar_l0_l3/eis_diagnostics.md`
- `reports/baselines/pulse_with_prior_eis_hgb50_report.json`
- `reports/baselines/capacity_with_prior_eis_hgb50_report.json`
- `reports/baselines/eis_prior_feature_claim_readiness.md`
- `docs/experiments/2026-05-23_eis_scalar_diagnostic_baselines.md`

Required Milestone 2.1.1 EIS claim-hardening artifacts:

- `reports/baselines/pulse_prior_eis_vs_best_noneis/paired_gain_vs_best_noneis.csv`
- `reports/baselines/pulse_prior_eis_vs_best_noneis/split_level_gain_vs_best_noneis.csv`
- `reports/baselines/pulse_prior_eis_vs_best_noneis/bootstrap_gain_vs_best_noneis.csv`
- `reports/baselines/pulse_prior_eis_vs_best_noneis/prior_eis_pulse_claim_readiness.md`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/paired_gain_vs_best_noneis.csv`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/split_level_gain_vs_best_noneis.csv`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/bootstrap_gain_vs_best_noneis.csv`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/prior_eis_capacity_claim_readiness.md`
- `reports/baselines/eis_alignment_sensitivity/pulse_prior_eis_alignment_summary.csv`
- `reports/baselines/eis_alignment_sensitivity/capacity_prior_eis_alignment_summary.csv`
- `reports/baselines/eis_alignment_sensitivity/eis_alignment_claim_readiness.md`
- `reports/baselines/eis_feature_completeness_sensitivity.csv`
- `reports/baselines/eis_feature_completeness_claim_readiness.md`
- `reports/baselines/eis_scalar_l0_l3/eis_self_endpoint_claim_readiness.md`
- `reports/baselines/eis_leakage_audit.md`
- `docs/experiments/2026-05-23_eis_claim_hardening.md`

Required Milestone 2.2 semi-empirical and replicate-gate artifacts:

- `reports/baselines/semi_empirical_capacity_report.json`
- `reports/baselines/semi_empirical_capacity/leaderboard.csv`
- `reports/baselines/semi_empirical_capacity/baseline_summary.md`
- `reports/baselines/semi_empirical_capacity/semi_empirical_claim_readiness.md`
- `reports/baselines/semi_empirical_capacity/comparisons/paired_gain_vs_hgb_f4.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/paired_gain_vs_best_stress.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/semi_empirical_comparison_summary.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/semi_empirical_comparison.md`
- `reports/analysis/replicate_uncertainty/replicate_spread_by_condition.csv`
- `reports/analysis/replicate_uncertainty/model_error_vs_replicate_spread.csv`
- `reports/analysis/replicate_uncertainty/condition_tolerance_intervals.csv`
- `reports/analysis/replicate_uncertainty/c_rate_replicate_uncertainty.md`
- `reports/analysis/replicate_uncertainty/replicate_uncertainty_summary.md`
- `reports/analysis/replicate_uncertainty/uncertainty_claim_readiness.md`
- `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md`

Required Milestone 2.3 grouped calibration artifacts:

- `reports/analysis/calibration_capacity/calibration_report.json`
- `reports/analysis/calibration_capacity/coverage_by_split.csv`
- `reports/analysis/calibration_capacity/coverage_by_condition.csv`
- `reports/analysis/calibration_capacity/interval_width_summary.csv`
- `reports/analysis/calibration_capacity/c_rate_calibration_summary.md`
- `reports/analysis/calibration_capacity/calibration_claim_readiness.md`
- `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md`

Required Milestone 1.2 checks:

- `mbp report build-manuscript-assets`
- `mbp report check-manuscript`
- `git diff --check`
- `ruff check . --no-cache` and `pytest -p no:cacheprovider` when reporting
  code is added or changed.

Milestone 1.3 `mbp report check-manuscript` must scan the continuous
manuscript, captions, generated tables, figure specifications, and source
traceability file.

Milestone 1.4 `mbp report check-reader-manuscript` must fail if reader-facing
prose contains raw claim IDs, allowed/blocked claim blocks, source-artifact
blocks, referenced-asset notes, or forbidden overclaim wording.
Milestone 1.4.1 extends that rule to fail on `Forbidden wording:` in the
reader-facing manuscript body.

Milestone 2.0 EIS validation commands:

- `mbp eis qa`
- `mbp eis alignment-sensitivity`
- `mbp eis build-features`
- `mbp eis feature-qa`
- `mbp eis claim-readiness`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.1.1 EIS validation commands:

- `mbp baseline compare-prior-eis-pulse`
- `mbp baseline compare-prior-eis-capacity`
- `mbp baseline eis-hardening-sensitivity`
- `mbp baseline eis-claim-readiness`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.2 validation commands:

- `mbp baseline run-semi-empirical`
- `mbp baseline compare-semi-empirical`
- `mbp analysis replicate-uncertainty`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.3 validation commands:

- `mbp analysis calibrate-capacity`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.1 EIS validation commands:

- `mbp eis build-targets`
- `mbp eis target-qa`
- `mbp baseline run-eis`
- focused `mbp baseline run-pulse` with prior-EIS groups
- focused `mbp baseline run-capacity` with prior-EIS groups
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 1.0 claim statuses must distinguish supported claims,
partially-supported claims, not-supported claims, gated claims, and blocked
claims. Unsupported claims must not be promoted by wording in paper-facing docs.

Allowed Milestone 0.5 targets:

- `capacity_Ah_k1`
- `delta_capacity_Ah`

Allowed Milestone 0.5 feature groups:

- `F0_time_only`
- `F1_state_time`
- `F2_state_exposure`
- `F3_state_nominal`
- `F4_state_log_age_scalar`

Allowed Milestone 0.6 stress-feature groups:

- `F5_log_age_histograms`
- `F6_coupled_stress`
- `F7_c_rate_focused`

Allowed Milestone 0.6.1 stress-feature groups:

- `F8_timestamp_weighted_stress`
- `F9_event_segmented_stress`
- `F10_c_rate_v1_1`

Allowed Milestone 0.6.3 narrow C-rate feature groups:

- `F11_minimal_cold_current`
- `F12_voltage_cold_current_interactions`
- `F13_sparse_c_rate_context`

`F0_time_only` is intentionally weak. Non-persistence learned baselines must
include prior check-up state through `capacity_Ah_k` in at least one state-aware
feature group.

Allowed Milestone 0.5 split views:

- `condition_fold`
- `temperature_holdout_fold`
- `c_rate_holdout_fold`
- `profile_holdout_fold`
- `voltage_window_holdout_fold`

Required Milestone 0.5 report artifacts:

- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`

Required Milestone 0.5b diagnostic artifacts:

- `baseline_diagnostics.md`
- `c_rate_holdout_error_analysis.md`
- `claim_readiness.md`
- `plots/feature_gain_by_split.csv`
- `plots/best_by_target_split.csv`
- `plots/c_rate_holdout_errors.csv`
- `plots/c_rate_holdout_by_condition.csv`
- `plots/c_rate_grouped_summaries.csv`

Milestone 0.5b linear baselines use train-fold numeric standardization for
`L1_ridge`. The standardization statistics must be fit on train rows only.

Milestone 0.5b quantile diagnostics for `L3_quantile_hist_gradient_boosting`
include:

- `q10_q90_interval_coverage`
- `q10_q90_interval_width_mean`
- `pinball_loss_q10`
- `pinball_loss_q50`
- `pinball_loss_q90`

Milestone 0.5c diagnostics for focused reports should compare against an L0
reference report when the focused report does not include persistence rows.
Missing references must be rendered explicitly as `reference_missing`; silent
`NA` values are not acceptable for L0 comparison fields.

Milestone 0.5c claim-readiness summaries are allowed to recommend the next
feature-engineering direction, but they do not authorize new modalities or
advanced models.

Milestone 0.6 stress-feature data products must remain modular sidecars keyed by
`cell_id`, `checkup_k`, and `checkup_k_next`. The baseline runner may join them
through `--stress-features`; the core interval table should remain stable.

Target-derived stress diagnostics such as `delta_capacity_per_day`,
`delta_capacity_per_efc`, and `delta_capacity_per_Ah_throughput` must not enter
predictive feature groups because they encode the capacity target.

Required Milestone 0.6 stress-feature artifacts:

- `data/interim/interval_stress_features_v1.parquet` (ignored generated data)
- `reports/audit/stress_feature_qa_report.json`
- `reports/baselines/capacity_stress_features_hgb50_report.json`
- `reports/baselines/capacity_stress_features_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_stress_features_hgb50/plots/stress_feature_gain_by_split.csv`
- `reports/baselines/capacity_stress_features_hgb50/plots/c_rate_stress_feature_errors.csv`
- `reports/baselines/capacity_stress_features_hgb50/plots/stress_feature_claim_readiness.csv`

Milestone 0.6 success criterion:

- improve C-rate `capacity_Ah_k1` condition-mean MAE below `0.125186`;
- improve C-rate `delta_capacity_Ah` condition-mean MAE below `0.101133`;
- avoid material degradation in `condition_fold` and
  `temperature_holdout_fold`.

Required Milestone 0.6.1 hardening artifacts:

- `reports/audit/current_sign_audit_report.json`
- `data/interim/interval_stress_features_v1_1.parquet` (ignored generated data)
- `reports/audit/stress_feature_v1_1_qa_report.json`
- `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

Milestone 0.6.1 success criterion:

- improve C-rate `capacity_Ah_k1` condition-mean MAE below `0.124656`;
- improve C-rate `delta_capacity_Ah` condition-mean MAE below `0.101133`;
- avoid material degradation in `condition_fold` and
  `temperature_holdout_fold`;
- do not promote sign-dependent charge features unless current-sign evidence is
  high confidence.

Required Milestone 0.6.2 diagnostic artifacts:

- `target_consistency_diagnostics.md`
- `c_rate_residual_analysis.md`
- `stress_feature_ablation_summary.md`
- `plots/derived_delta_from_capacity_metrics.csv`
- `plots/derived_capacity_from_delta_metrics.csv`
- `plots/direct_vs_derived_target_metrics.csv`
- `plots/c_rate_residuals_by_parameter_set.csv`
- `plots/c_rate_residuals_by_temperature.csv`
- `plots/c_rate_residuals_by_voltage_window.csv`
- `plots/c_rate_residuals_by_capacity_bin.csv`
- `plots/c_rate_residuals_by_interval_count.csv`
- `plots/c_rate_signed_error_summary.csv`
- `plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`
- `plots/c_rate_gain_by_feature_group.csv`

Milestone 0.6.2 must not retrain by default. It should use existing row-level
prediction Parquet files and JSON reports to decide whether direct delta,
derived delta from capacity, or both target paths should be reported.

Required Milestone 0.6.3 diagnostic artifacts:

- `reports/baselines/capacity_delta_rate_targets_hgb50_report.json`
- `reports/baselines/capacity_delta_rate_targets_hgb50/plots/rate_target_vs_direct_delta.csv`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_c_rate_bias_corrected_report.json`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/bias_correction_by_split.csv`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/c_rate_bias_before_after.csv`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`

Milestone 0.6.3 may train on normalized target modes
`delta_capacity_per_day_target` and `delta_capacity_per_efc_target`, but the
report metrics must evaluate predictions back in `delta_capacity_Ah` units. The
true target-derived rates must never enter predictive input feature groups.
Residual correction must be fit inside each train fold only; test-fold
residuals must not be used for correction.

Required Milestone 0.7 PULSE artifacts:

- `docs/PULSE_TARGET_POLICY.md`
- `reports/audit/pulse_qa_report.json`
- `reports/audit/pulse_alignment_report.json`
- `reports/audit/pulse_target_coverage.csv`
- `data/interim/pulse_target_table.parquet` (ignored generated data)
- `reports/baselines/pulse_resistance_l0_l3_report.json`
- `reports/baselines/pulse_resistance_l0_l3/leaderboard.csv`
- `reports/baselines/pulse_resistance_l0_l3/baseline_summary.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_diagnostics.md`

Allowed Milestone 0.7 PULSE targets:

- `delta_pulse_1s_resistance`
- `pulse_1s_resistance_k1`
- `delta_pulse_10ms_resistance`
- `pulse_10ms_resistance_k1`

Allowed Milestone 0.7 PULSE feature groups:

- `P0_persistence`
- `P1_state_time`
- `P2_state_capacity`
- `P3_state_nominal`
- `P4_state_log_age_scalar`
- `P5_stress_v1_1`

Milestone 0.7 reports must use grouped split views and report target coverage.
PULSE results are resistance-baseline diagnostics only; they are not evidence
for a capacity+PULSE multimodal claim.

Required Milestone 0.7.1 PULSE hardening artifacts:

- `reports/audit/pulse_alignment_sensitivity_report.json`
- `reports/audit/pulse_alignment_sensitivity_coverage.csv`
- `reports/audit/pulse_missing_canonical_targets.csv`
- `reports/audit/pulse_missingness_by_condition.csv`
- `reports/audit/pulse_missingness_by_split.csv`
- `data/interim/pulse_target_table_mean.parquet` (ignored generated data)
- `data/interim/pulse_target_table_charge.parquet` (ignored generated data)
- `data/interim/pulse_target_table_discharge.parquet` (ignored generated data)
- `reports/baselines/pulse_resistance_alignment_24h_report.json`
- `reports/baselines/pulse_resistance_alignment_36h_report.json`
- `reports/baselines/pulse_resistance_alignment_sensitivity/baseline_summary.md`
- `reports/baselines/pulse_resistance_alignment_sensitivity/plots/pulse_alignment_threshold_comparison.csv`
- `reports/baselines/pulse_resistance_direction_mean_report.json`
- `reports/baselines/pulse_resistance_direction_charge_report.json`
- `reports/baselines/pulse_resistance_direction_discharge_report.json`
- `reports/baselines/pulse_resistance_l0_l3/pulse_resistance_direction_comparison.md`
- `reports/baselines/pulse_resistance_l0_l3/plots/pulse_direction_comparison.csv`

Milestone 0.7.1 direction policy:

- `mean` remains the canonical PULSE target direction handling.
- `charge` and `discharge` target tables are diagnostic until a later policy
  accepts direction-specific targets.
- If a direction-specific table has no finite adjacent interval targets, the
  baseline report must emit an explicit warning rather than silently passing.

Milestone 0.7.1 alignment policy:

- Baselines may use `--max-alignment-delta-s` to filter intervals where either
  endpoint exceeds the threshold.
- Alignment-threshold reports must include retained interval counts, retained
  cell/parameter-set counts, and split coverage.
- Large-alignment rows are still warnings, not silent exclusions, unless a
  later PULSE target policy changes the canonical target definition.

Required Milestone 0.7.2 PULSE robustness artifacts:

- `reports/baselines/pulse_resistance_l0_l3/pulse_claim_readiness.md`
- `reports/baselines/pulse_resistance_target_robustness_report.json`
- `reports/baselines/pulse_resistance_target_robustness/leaderboard.csv`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_1s_vs_10ms_comparison.csv`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_delta_vs_k1_comparison.csv`
- `reports/baselines/pulse_resistance_alignment_robustness.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`
- `reports/audit/pulse_missingness_interpretation.md`
- `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`

Milestone 0.7.2 target policy:

- `delta_pulse_1s_resistance` remains the canonical first PULSE transition
  target unless target robustness shows a clear replacement.
- `delta_pulse_10ms_resistance`, `pulse_1s_resistance_k1`, and
  `pulse_10ms_resistance_k1` may be evaluated as scalar diagnostic targets.
- k1 resistance-level targets must be interpreted as state-tracking targets,
  not direct transition prediction.
- Direction-specific claims remain blocked; current RT/50 `mean` is documented
  as effectively equivalent to `charge` in the available generated target table.

Required Milestone 0.8 coupling artifacts:

- `data/interim/capacity_pulse_coupling_table.parquet` (ignored generated data)
- `reports/coupling/pulse_capacity/pulse_capacity_correlation.md`
- `reports/coupling/pulse_capacity/plots/capacity_residual_vs_delta_pulse.csv`
- `reports/coupling/pulse_capacity/plots/capacity_residual_by_pulse_growth_bin.csv`
- `reports/coupling/pulse_capacity/plots/c_rate_capacity_residual_by_pulse_growth.csv`
- `reports/coupling/pulse_capacity/plots/pulse_growth_by_capacity_error_decile.csv`
- `reports/baselines/capacity_with_prior_pulse_hgb50_report.json`
- `reports/baselines/capacity_with_prior_pulse_hgb50/pulse_feature_gain.md`
- `reports/baselines/capacity_with_prior_pulse_hgb50/plots/capacity_pulse_feature_gain_by_split.csv`
- `reports/baselines/capacity_with_prior_pulse_hgb50/plots/c_rate_capacity_pulse_feature_gain.csv`
- `reports/baselines/capacity_with_prior_pulse_hgb50/plots/pulse_feature_gain_claim_readiness.csv`
- `docs/experiments/2026-05-23_capacity_pulse_coupling_diagnostics.md`

Milestone 0.8 feature policy:

- Capacity baselines may use prior PULSE state at check-up `k`.
- `pulse_1s_resistance_k1`, `delta_pulse_1s_resistance`,
  `pulse_10ms_resistance_k1`, and `delta_pulse_10ms_resistance` must not enter
  capacity predictive feature groups.
- Any apparent gain from future PULSE deltas is leakage and is not publishable
  evidence.

Required Milestone 0.8.1 coupling robustness artifacts:

- `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/`
- `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah/`
- `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate/`
- `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate/`
- `canonical_model_correlation.md`
- `interval_level_correlation.md`
- `condition_level_correlation.md`
- `bootstrap_correlation_summary.md`
- `residualized_correlation.md`
- `subgroup_coupling_summary.md`
- `coupling_claim_readiness.md`
- `plots/canonical_model_residual_vs_pulse.csv`
- `plots/canonical_model_correlation_by_split.csv`
- `plots/interval_level_pulse_capacity_correlation.csv`
- `plots/condition_level_pulse_capacity_correlation.csv`
- `plots/pulse_capacity_correlation_bootstrap.csv`
- `plots/residualized_pulse_capacity_correlation.csv`
- `plots/subgroup_pulse_capacity_correlation.csv`
- `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md`

Milestone 0.8.1 decision rule:

- Coupling evidence may be described as scalar explanatory diagnostics when it
  survives canonical-model filtering and interval/condition aggregation.
- Predictive capacity+PULSE claims remain blocked unless a later non-neural
  baseline demonstrates grouped predictive gains without future PULSE leakage.

Required Milestone 0.9 prior-PULSE predictive artifacts:

- `reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_report.json`
- `reports/baselines/capacity_prior_pulse_predictive/paired_condition_gain.csv`
- `reports/baselines/capacity_prior_pulse_predictive/split_level_gain_summary.csv`
- `reports/baselines/capacity_prior_pulse_predictive/c_rate_gain_summary.csv`
- `reports/baselines/capacity_prior_pulse_predictive/coverage_effect_summary.csv`
- `reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_claim_readiness.md`
- `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md`

Milestone 0.9 claim rules:

- Primary target: `capacity_Ah_k1`.
- Secondary guardrail: `delta_capacity_Ah`.
- If `capacity_Ah_k1` gains are positive and robust while
  `delta_capacity_Ah` gains are not, only a narrow capacity-level prediction
  claim is allowed.
- Do not claim interval fade-rate improvement unless `delta_capacity_Ah`
  improves under paired grouped validation.
- Future PULSE state and PULSE deltas invalidate the result if they enter
  capacity feature groups.

Required Milestone 0.9.1 strongest non-PULSE comparison artifacts:

- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_report.json`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/paired_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/c_rate_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/bootstrap_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md`
- `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`

Milestone 0.9.1 claim rules:

- If prior PULSE beats the strongest supplied non-PULSE baseline for
  `capacity_Ah_k1` with bootstrap p05 above zero in C-rate and at least one
  other OOD split, a narrow prior-PULSE level-prediction claim is allowed.
- If prior PULSE beats F4 but not the strongest supplied non-PULSE baseline,
  report only the F4 improvement.
- If `delta_capacity_Ah` remains negative, fade-rate prediction claims remain
  blocked.

Blocked until later milestones:

- EIS claims and PULSE scientific claims beyond scalar resistance baselines.
- Sequence models, neural models, policy ranking, and CBAT architecture.
